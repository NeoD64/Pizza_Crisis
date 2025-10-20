from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from Model import DiscountCode

CENTS = Decimal("0.01")

def round_money(x: Decimal) -> Decimal:
    return x.quantize(CENTS, rounding=ROUND_HALF_UP)

class DiscountAndLoyaltyManager:
    """
    Pricing policy (in order):
      1) Birthday: subtract the cheapest pizza's *base* price if today is the customer's birthday.
      2) Loyalty: 10% off if customer has bought >= 10 pizzas in completed/paid orders historically.
      3) Discount code: percentage off if valid; mark as used only when for_checkout=True.
    All calculations use Decimal and round to cents each step.
    """

    LOYALTY_COMPLETED_STATUSES = {"COMPLETED", "PAID", "FULFILLED"}

    def __init__(self, customer, order, discount_code=None, now: datetime | None = None):
        self.customer = customer
        self.order = order
        self.discount_code = discount_code
        # tz-aware current time (UTC) for consistent comparisons
        self.now = now or datetime.now(timezone.utc)


    def apply_all_discounts(self, db_session, *, for_checkout: bool = False):
        """
        Recompute total and applied discounts from the current order state.
        If for_checkout=True, the discount code (if valid) is consumed (is_used=True) in the same txn.
        Returns: (final_total: Decimal, applied_discounts: list[str], invalid_code: bool)
        """
        return self._calculate(db_session, for_checkout=for_checkout)


    def _calculate(self, db_session, *, for_checkout: bool):
        applied = []
        invalid_code = False

        # Base total (sum of *base* pizza prices)
        base_prices = [self._pizza_base_amount(p) for p in self.order.pizzas]
        total = round_money(sum(base_prices, Decimal("0.00")))

        # 1) Birthday (free cheapest base pizza)
        if self._is_birthday_today():
            cheapest = min(base_prices, default=Decimal("0.00"))
            if cheapest > 0:
                total = round_money(max(Decimal("0.00"), total - cheapest))
                applied.append("🎂 Birthday Free Pizza!")

        # 2) Loyalty (-10%) after 10 historical pizzas
        if self._historical_pizza_count() >= 10:
            total = round_money(total * Decimal("0.90"))
            applied.append("⭐ 10% Loyalty Discount")

        # 3) Discount code (%)
        if self.discount_code:
            code_obj = (
                db_session.query(DiscountCode)
                .filter_by(code=self.discount_code)
                .with_for_update(read=True) if for_checkout else
                db_session.query(DiscountCode).filter_by(code=self.discount_code)
            ).first()

            if not code_obj:
                applied.append("❌ Invalid discount code")
                invalid_code = True
            elif getattr(code_obj, "is_used", False):
                applied.append("❌ Code already used")
                invalid_code = True
            elif self._is_expired(code_obj.expires_at):
                applied.append("❌ Code expired")
                invalid_code = True
            else:
                pct = Decimal(str(code_obj.discount_percentage)) / Decimal("100")
                pct = max(Decimal("0"), min(pct, Decimal("1")))
                total = round_money(total * (Decimal("1") - pct))
                applied.append(f"✅ {code_obj.discount_percentage}% Discount Applied")

                if for_checkout:
                    code_obj.is_used = True
                    db_session.add(code_obj)

        total = round_money(max(Decimal("0.00"), total))
        return total, applied, invalid_code


    def _historical_pizza_count(self) -> int:
        """
        Count pizzas in customer orders that are considered completed/paid.
        Does NOT include the current open order.
        """
        orders = getattr(self.customer, "orders", []) or []
        total = 0
        for o in orders:
            status = getattr(o, "status", None)
            if status in self.LOYALTY_COMPLETED_STATUSES:
                total += len(getattr(o, "pizzas", []) or [])
        return total

    def _is_birthday_today(self) -> bool:
        bd = getattr(self.customer, "birthdate", None)
        if not isinstance(bd, date):
            return False

        today = self.now.date()

        # Feb-29 policy: celebrate on Feb-29 in leap years, otherwise Feb-28
        if bd.month == 2 and bd.day == 29:
            if self._is_leap_year(today.year):
                return today.month == 2 and today.day == 29
            return today.month == 2 and today.day == 28

        # Normal birthdays
        return bd.month == today.month and bd.day == today.day

    @staticmethod
    def _is_leap_year(y: int) -> bool:
        return (y % 4 == 0) and ((y % 100 != 0) or (y % 400 == 0))

    def _is_expired(self, expires_at) -> bool:
        """
        Handle both naive and aware datetimes gracefully (assume naive=UTC).
        If None, treat as non-expiring.
        """
        if expires_at is None:
            return False
        if isinstance(expires_at, datetime):
            if expires_at.tzinfo is None:
                exp = expires_at.replace(tzinfo=timezone.utc)
            else:
                exp = expires_at.astimezone(timezone.utc)
            return exp <= self.now.astimezone(timezone.utc)
        # If it's a date, expire at end-of-day UTC
        if isinstance(expires_at, date):
            eod = datetime(expires_at.year, expires_at.month, expires_at.day, 23, 59, 59, tzinfo=timezone.utc)
            return eod <= self.now.astimezone(timezone.utc)
        return True  # unknown type => treat as expired

    @staticmethod
    def _pizza_base_amount(pizza) -> Decimal:
        """
        Extract the true price for discount calculation.
        Uses final_amount() if available for consistency with UI subtotal.
        This ensures subtotal and final_total match when no discounts apply.
        """
        # Prefer final_amount() since your route uses it for subtotal
        if hasattr(pizza, "final_amount"):
            fa = getattr(pizza, "final_amount")
            return Decimal(str(fa() if callable(fa) else fa))

        # Fallbacks in case some pizza objects don't have final_amount
        for attr in ("base_amount", "base_price", "price"):
            if hasattr(pizza, attr):
                return Decimal(str(getattr(pizza, attr)))
        for meth in ("base_amount", "base_price", "price"):
            v = getattr(pizza, meth, None)
            if callable(v):
                return Decimal(str(v()))
        return Decimal("0.00")

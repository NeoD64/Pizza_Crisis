from datetime import date, datetime
from Model import DiscountCode


class DiscountAndLoyaltyManager:
    def __init__(self, customer, order, discount_code=None):
        self.customer = customer
        self.order = order
        self.discount_code = discount_code
        self.applied_discounts = []
        self.final_total = order.total_amount  # base order total
        self.invalid_code = False

    def apply_loyalty_discount(self):
        """10% off after 10 pizzas bought throughout history."""
        total_pizzas = sum(len(order.pizzas) for order in self.customer.orders)
        if total_pizzas >= 10:
            self.final_total *= 0.90
            self.applied_discounts.append("⭐ 10% Loyalty Discount")

    def apply_birthday_discount(self):
        """Free pizza on customer birthday (cheapest pizza in order)."""
        today = date.today()
        if (
            self.customer.birthdate.month == today.month
            and self.customer.birthdate.day == today.day
        ):
            cheapest = min((p.final_amount() for p in self.order.pizzas), default=0)
            if cheapest > 0:
                self.final_total -= cheapest
                self.applied_discounts.append("🎂 Birthday Free Pizza!")

    def apply_discount_code(self, db_session):
        """One-time discount code with DB validation."""
        if not self.discount_code:
            return

        code_obj = db_session.query(DiscountCode).filter_by(code=self.discount_code).first()

        if not code_obj:
            self.applied_discounts.append("❌ Invalid discount code")
            self.invalid_code = True
            return

        if code_obj.is_used:
            self.applied_discounts.append("❌ Code already used")
            self.invalid_code = True
            return

        if code_obj.expires_at <= datetime.now():
            self.applied_discounts.append("❌ Code expired")
            self.invalid_code = True
            return

        self.final_total *= (1 - code_obj.discount_percentage / 100)
        self.applied_discounts.append(f"✅ {code_obj.discount_percentage}% Discount Applied")
        code_obj.is_used = True
        db_session.commit()

    def apply_all_discounts(self, db_session):
        """Apply loyalty → birthday → code."""
        self.apply_loyalty_discount()
        self.apply_birthday_discount()
        self.apply_discount_code(db_session)
        return self.final_total, self.applied_discounts

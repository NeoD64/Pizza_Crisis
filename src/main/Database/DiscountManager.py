from datetime import data

from src.main.Database.Model import DiscountCode


class DiscountAndLoyaltyManager:
        def __innit__(self, customer,order,discount_code=None):
            self.customer=customer
            self.order=order
            self.discount_code=discount_code
            self.applied_discounts = []


        def apply_loyalty_discount(self):
            """ 10% off after 10 pizzas bought through-out the history """
            total_pizzas = 0
            for order in self.customer.order:
                for order_item in order.order_items:
                    total_pizzas += order_item.quantity

            if total_pizzas >= 10:
                # apply 10% off
                self.order.total_amount *= 0.90
                self.applied_discounts.append("10% Loyalty Discount")


        def apply_discount_code(self, db_session):
            """ one-time discount code """
            if self.discount_code:
                code_obj = db_session.query(DiscountCode).filter_by(code=self.discount_code).first()
                    if code_obj:
                         self.order.total_amount *= (1 - code_obj.discount_percentage / 100)
                         self.applied_discounts.append(f"{code_obj.discount_percentage}% Discount Code")
                         db_session.delete(code_obj)  #one-time use only
                         db_session.commit()
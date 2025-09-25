from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(50), unique=True, nullable=False)
    birthdate = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(250), nullable=False)
    postal_code = db.Column(db.String(10), nullable=False)

    orders = db.relationship("Order", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer {self.id} {self.first_name} {self.last_name}>"


class DiscountCode(db.Model):
    __tablename__ = 'discountcode'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percentage = db.Column(db.Float, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, nullable=False)

    orders = db.relationship("Order", back_populates="discount")

    def __repr__(self):
        return f"<DiscountCode {self.code} - {self.discount_percentage}%>"


class DeliveryPerson(db.Model):
    __tablename__ = "deliveryperson"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(50), unique=True, nullable=False)
    postal_code = db.Column(db.String(10), nullable=False)

    orders = db.relationship("Order", back_populates="delivery_person")

    def __repr__(self):
        return f"<DeliveryPerson {self.id} {self.first_name} {self.last_name}>"


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default="Pending")  # Pending, Delivered, etc.

    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    discount_id = db.Column(db.Integer, db.ForeignKey('discountcode.id'))
    delivery_person_id = db.Column(db.Integer, db.ForeignKey('deliveryperson.id'))

    customer = db.relationship("Customer", back_populates="orders")
    discount = db.relationship("DiscountCode", back_populates="orders")
    delivery_person = db.relationship("DeliveryPerson", back_populates="orders")

    pizzas = db.relationship("Pizza", secondary="order_pizzas", back_populates="orders")
    drinks = db.relationship("Drink", secondary="order_drinks", back_populates="orders")
    desserts = db.relationship("Dessert", secondary="order_desserts", back_populates="orders")

    @property
    def total_amount(self):
        return (
            sum(pizza.final_amount() for pizza in self.pizzas)
            + sum(drink.drink_price for drink in self.drinks)
            + sum(dessert.dessert_price for dessert in self.desserts)
        )

    def __repr__(self):
        return f"<Order {self.id} - Customer {self.customer_id}>"


class OrderPizza(db.Model):
    __tablename__ = 'order_pizzas'
    order_id = db.Column(db.ForeignKey('orders.id'), primary_key=True)
    pizza_id = db.Column(db.ForeignKey('pizza.id'), primary_key=True)

class OrderDrink(db.Model):
    __tablename__ = 'order_drinks'
    order_id = db.Column(db.ForeignKey('orders.id'), primary_key=True)
    drink_id = db.Column(db.ForeignKey('drinks.id'), primary_key=True)


class OrderDessert(db.Model):
    __tablename__ = 'order_desserts'
    order_id = db.Column(db.ForeignKey('orders.id'), primary_key=True)
    dessert_id = db.Column(db.ForeignKey('desserts.id'), primary_key=True)


class Pizza(db.Model):
    __tablename__ = 'pizza'
    id = db.Column(db.Integer, primary_key=True)
    pizza_name = db.Column(db.String(100), unique=True, nullable=False)
    base_price = db.Column(db.Float, nullable=False)  # ✅ stored in DB

    ingredients = db.relationship("Ingredient", secondary="pizzaingredient", back_populates="pizzas")
    orders = db.relationship("Order", secondary="order_pizzas", back_populates="pizzas")

    def ingredient_cost(self) -> float:
        """Sum of all ingredient prices linked to this pizza."""
        return sum(ingredient.ingredient_price for ingredient in self.ingredients)

    def subtotal(self) -> float:
        """Base price + ingredient costs (before margin/tax)."""
        return self.base_price + self.ingredient_cost()

    def final_amount(self) -> float:
        """
        Final selling price:
        (base price + ingredient costs) → add 40% margin → add 9% tax.
        """
        margin = self.subtotal() * 1.4
        return round(margin * 1.09, 2)

    def __repr__(self):
        return f"<Pizza {self.id} - {self.pizza_name}>"


class Ingredient(db.Model):
    __tablename__ = 'ingredient'
    id = db.Column(db.Integer, primary_key=True)
    ingredient_name = db.Column(db.String(100), nullable=False)
    ingredient_price = db.Column(db.Float, nullable=False)

    pizzas = db.relationship("Pizza", secondary="pizzaingredient", back_populates="ingredients")  # ✅ fixed

    def __repr__(self):
        return f"<Ingredient {self.id} - {self.ingredient_name}>"


class Drink(db.Model):
    __tablename__ = 'drinks'
    id = db.Column(db.Integer, primary_key=True)
    drink_name = db.Column(db.String(100), nullable=False)
    drink_price = db.Column(db.Float, nullable=False)

    orders = db.relationship("Order", secondary="order_drinks", back_populates="drinks")

    def __repr__(self):
        return f"<Drink {self.id} - {self.drink_name}>"


class Dessert(db.Model):
    __tablename__ = 'desserts'
    id = db.Column(db.Integer, primary_key=True)
    dessert_name = db.Column(db.String(100), nullable=False)
    dessert_price = db.Column(db.Float, nullable=False)

    orders = db.relationship("Order", secondary="order_desserts", back_populates="desserts")

    def __repr__(self):
        return f"<Dessert {self.id} - {self.dessert_name}>"


class PizzaIngredient(db.Model):
    __tablename__ = 'pizzaingredient'  # ✅ matches your DB
    pizza_id = db.Column(db.ForeignKey('pizza.id'), primary_key=True)
    ingredient_id = db.Column(db.ForeignKey('ingredient.id'), primary_key=True)


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Payment {self.id} - {self.amount}>"

from datetime import datetime
import flask_sqlalchemy
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    phone_number = db.Column(db.String(50), unique=True, nullable=False)

    orders = db.relationship("Order", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Customer {self.id} {self.email}>"

class DiscountCode(db.Model):
    __tablename__ = 'discount_codes'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percentage = db.Column(db.Float, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    orders = db.relationship("Order", back_populates="discount")

    def __repr__(self):
        return f"<DiscountCode {self.code} - {self.discount_percentage}%>"

class DeliveryPerson(db.Model):
    __tablename__ = 'delivery_persons'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(50), unique=True, nullable=False)

    orders = db.relationship("Order", back_populates="delivery_person")

    def __repr__(self):
        return f"<DeliveryPerson {self.id} {self.phone_number}>"

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)


    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    discount_id = db.Column(db.Integer, db.ForeignKey('discount_codes.id'))
    delivery_person_id = db.Column(db.Integer, db.ForeignKey('delivery_persons.id'))


    customer = db.relationship("Customer", back_populates="orders")
    discount = db.relationship("DiscountCode", back_populates="orders")
    delivery_person = db.relationship("DeliveryPerson", back_populates="orders")

    def __repr__(self):
        return f'<Order {self.id} - Customer {self.customer_id}>'

class OrderPizza(db.Model):
    __tablename__ = 'order_items'
    order_id = db.Column(db.ForeignKey('orders.id'), primary_key=True)
    pizza_id = db.Column(db.ForeignKey('pizzas.id'), primary_key=True)



class Pizza(db.Model):
    __tablename__ = 'pizzas'
    id = db.Column(db.Integer, primary_key=True)
    pizza_name = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return f"<Pizza {self.id} - {self.pizza_name}>"

class Ingredient(db.Model):
    __tablename__ = 'ingredients'
    id = db.Column(db.Integer, primary_key=True)
    ingredient_name = db.Column(db.String(100), nullable=False)
    ingredient_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<Ingredient {self.id} - {self.ingredient_name}>"

class PizzaIngredient(db.Model):
    __tablename__ = 'pizza_ingredients'
    pizza_id = db.Column(db.ForeignKey('pizzas.id'), primary_key=True)
    ingredient_id = db.Column(db.ForeignKey('ingredients.id'), primary_key=True)

class Payement(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    amount = db.Column(db.Float, nullable=False)
    payement_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Payment {self.id} - {self.Amount}>"


from datetime import datetime
import enum
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class GenderEnum(enum.Enum):
    MALE = 'Male'
    FEMALE = 'Female'
    OTHER = 'Other'
    PREFER_NOT_TO_SAY = 'Prefer not to say'

pizzaingredient = db.Table('pizzaingredient',
    db.Column('pizza_id', db.Integer, db.ForeignKey('pizza.id'), primary_key=True),
    db.Column('ingredient_id', db.Integer, db.ForeignKey('ingredient.id'), primary_key=True)
)


class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(50), unique=True, nullable=False)
    birthdate = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(250), nullable=False)
    postal_code = db.Column(db.String(10), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.Enum(GenderEnum), nullable=True, default=GenderEnum.PREFER_NOT_TO_SAY)

    is_staff = db.Column(db.Boolean, nullable=False, default=False)

    orders = db.relationship("Order", back_populates="customer", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
    available_at = db.Column(db.DateTime, nullable=False)

    orders = db.relationship("Order", back_populates="delivery_person")

    def __repr__(self):
        return f"<DeliveryPerson {self.id} {self.first_name} {self.last_name}>"


class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    estimated_delivery_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(
        db.Enum('PENDING', 'PENDING_ASSIGNMENT', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED'),
        default='PENDING'
    )


    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    discount_id = db.Column(db.Integer, db.ForeignKey('discountcode.id'))
    delivery_person_id = db.Column(db.Integer, db.ForeignKey('deliveryperson.id'))

    customer = db.relationship("Customer", back_populates="orders")
    discount = db.relationship("DiscountCode", back_populates="orders")
    delivery_person = db.relationship("DeliveryPerson", back_populates="orders")

    pizzas = db.relationship("OrderPizza", back_populates="order", cascade="all, delete-orphan")
    drinks = db.relationship("OrderDrink", back_populates="order", cascade="all, delete-orphan")
    desserts = db.relationship("OrderDessert", back_populates="order", cascade="all, delete-orphan")

    @property
    def total_amount(self):
        pizza_total = sum(
            pizza_assoc.pizza.final_amount() * pizza_assoc.quantity for pizza_assoc in self.pizzas)
        drink_total = sum(
            drink_assoc.drink.drink_price * drink_assoc.quantity for drink_assoc in self.drinks)
        dessert_total = sum(
            dessert_assoc.dessert.dessert_price * dessert_assoc.quantity for dessert_assoc in self.desserts)
        return pizza_total + drink_total + dessert_total

    def __repr__(self):
        return f"<Order {self.id} - Customer {self.customer_id}>"


class OrderPizza(db.Model):
    __tablename__ = 'order_pizzas'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    pizza_id = db.Column(db.Integer, db.ForeignKey('pizza.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)

    order = db.relationship("Order", back_populates="pizzas")
    pizza = db.relationship("Pizza", back_populates="order")



class OrderDrink(db.Model):
    __tablename__ = 'order_drinks'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    drink_id = db.Column(db.Integer, db.ForeignKey('drinks.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    order = db.relationship("Order", back_populates="drinks")
    drink = db.relationship("Drink", back_populates="order")


class OrderDessert(db.Model):
    __tablename__ = 'order_desserts'
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), primary_key=True)
    dessert_id = db.Column(db.Integer, db.ForeignKey('desserts.id'), primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    order = db.relationship("Order", back_populates="desserts")
    dessert = db.relationship("Dessert", back_populates="order")

class Pizza(db.Model):
    __tablename__ = 'pizza'
    id = db.Column(db.Integer, primary_key=True)
    pizza_name = db.Column(db.String(100), unique=True, nullable=False)
    base_price = db.Column(db.Float, nullable=False)

    category = db.Column(db.String(20), default="Normal") # "Normal", "Vegetarian", "Vegan"

    ingredients = db.relationship("Ingredient", secondary=pizzaingredient, back_populates="pizzas")
    order= db.relationship("OrderPizza", back_populates="pizza", cascade="all, delete-orphan")


    def ingredient_cost(self):
        return sum(i.ingredient_price for i in self.ingredients)

    def subtotal(self):
        return self.base_price + self.ingredient_cost()

    def final_amount(self):
        margin = self.subtotal() * 1.4
        return round(margin * 1.09, 2)

    def __repr__(self):
        return f"<Pizza {self.id} - {self.pizza_name} ({self.category})>"



class Ingredient(db.Model):
    __tablename__ = 'ingredient'
    id = db.Column(db.Integer, primary_key=True)
    ingredient_name = db.Column(db.String(100), nullable=False)
    ingredient_price = db.Column(db.Float ,CheckConstraint('ingredient_price >= 0',name='check_positive_price'), nullable=False )

    pizzas = db.relationship("Pizza", secondary=pizzaingredient, back_populates="ingredients")

    def __repr__(self):
        return f"<Ingredient {self.id} - {self.ingredient_name}>"


class Drink(db.Model):
    __tablename__ = 'drinks'
    id = db.Column(db.Integer, primary_key=True)
    drink_name = db.Column(db.String(100), nullable=False)
    drink_price = db.Column(db.Float, nullable=False)

    order = db.relationship("OrderDrink", back_populates="drink", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Drink {self.id} - {self.drink_name}>"


class Dessert(db.Model):
    __tablename__ = 'desserts'
    id = db.Column(db.Integer, primary_key=True)
    dessert_name = db.Column(db.String(100), nullable=False)
    dessert_price = db.Column(db.Float, nullable=False)

    order = db.relationship("OrderDessert", back_populates="dessert", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Dessert {self.id} - {self.dessert_name}>"


class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Payment {self.id} - {self.amount}>"

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    phone_number = db.Column(db.String(50), unique=True, nullable=False)

    orders = db.relationship("Order", back_populates="customer")

    def __repr__(self):
        return f'<Customer {self.id} {self.email}>'


class DiscountCode(db.Model):
    __tablename__ = 'discount_codes'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percentage = db.Column(db.Float, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    orders = db.relationship("Order", back_populates="discount")

    def __repr__(self):
        return f'<DiscountCode {self.code} - {self.discount_percentage}%>'


class DeliveryPerson(db.Model):
    __tablename__ = 'delivery_persons'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(50), unique=True, nullable=False)

    orders = db.relationship("Order", back_populates="delivery_person")

    def __repr__(self):
        return f'<DeliveryPerson {self.id} {self.phone_number}>'

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)

    # - Foreign keys
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    discount_id = db.Column(db.Integer, db.ForeignKey('discount_codes.id'))
    delivery_person_id = db.Column(db.Integer, db.ForeignKey('delivery_persons.id'))

    # - Relationships
    customer = db.relationship("Customer", back_populates="orders")
    discount = db.relationship("DiscountCode", back_populates="orders")
    delivery_person = db.relationship("DeliveryPerson", back_populates="orders")

    def __repr__(self):
        return f'<Order {self.id} - Customer {self.customer_id}>'

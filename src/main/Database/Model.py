from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    first_name=db.Column(db.String(100), nullable=False)
    last_name=db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    phone_number = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Customer {self.id}{self.email}{self.phone_number}>'

class DiscountCode(db.Model):
    __tablename__ = 'discount_codes'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percentage = db.Column(db.Float, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f'<DiscountCode {self.code} - {self.discount_percentage}%>'

class DeliveryPerson(db.Model):
    __tablename__ = 'delivery_persons'
    id = db.Column(db.Integer, primary_key=True)
    first_name=db.Column(db.String(100), nullable=False)
    last_name=db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(50), unique=True, nullable=False)


    def __repr__(self):
        return f'<DeliveryPerson {self.id}{self.phone_number}>'

class Order(db.Model):
    __tablename__ = 'orders'
    id = db.Column(db.Integer, primary_key=True)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)

    customer_id= db.relationship("Customer", back_populates="order",cascade="all, delete-orphan")
    discount_id= db.relationship("DiscountCode", back_populates="order",cascade="all, delete-orphan")
    delivery_person_id= db.relationship("DeliveryPerson", back_populates="order",cascade="all, delete-orphan")


    def __repr__(self):
        return f'<Order {self.id} - Customer {self.customer_id} - Status {self.status}>'


from flask import Flask
from Model import db, Customer, DiscountCode, DeliveryPerson, Order, Pizza, Ingredient, Drink, Dessert, PizzaIngredient, Payment
from dotenv import load_dotenv
import os
from routes import bp
from datetime import datetime, date, timedelta

def seed_db():
    """seeding data in the database"""
    if not Ingredient.query.first():
        cheese = Ingredient(ingredient_name="Cheese", ingredient_price=1.0)
        tomato = Ingredient(ingredient_name="Tomato Sauce", ingredient_price=0.5)
        pepperoni = Ingredient(ingredient_name="Pepperoni", ingredient_price=1.5)
        mushroom = Ingredient(ingredient_name="Mushrooms", ingredient_price=1.2)
        onion = Ingredient(ingredient_name="Onion", ingredient_price=0.8)
        olives = Ingredient(ingredient_name="Olives", ingredient_price=1.0)
        db.session.add_all([cheese, tomato, pepperoni, mushroom, onion, olives])
        db.session.commit()

    if not Pizza.query.first():
        margherita = Pizza(pizza_name="Margherita")
        pepperoni_pizza = Pizza(pizza_name="Pepperoni Pizza")
        veggie = Pizza(pizza_name="Veggie")
        db.session.add_all([margherita, pepperoni_pizza, veggie])
        db.session.commit()

        cheese = Ingredient.query.filter_by(ingredient_name="Cheese").first()
        tomato = Ingredient.query.filter_by(ingredient_name="Tomato Sauce").first()
        pepperoni = Ingredient.query.filter_by(ingredient_name="Pepperoni").first()
        mushroom = Ingredient.query.filter_by(ingredient_name="Mushrooms").first()
        onion = Ingredient.query.filter_by(ingredient_name="Onion").first()
        olives = Ingredient.query.filter_by(ingredient_name="Olives").first()

        margherita.ingredients.extend([cheese,tomato])
        pepperoni_pizza.ingredients.extend([cheese, tomato, pepperoni])
        veggie.ingredients.extend([cheese, tomato, mushroom, onion, olives])
        db.session.commit()

    if not Drink.query.first():
        cola = Drink(drink_name="Cola", drink_price=2.5)
        water = Drink(drink_name="Water", drink_price=1.0)
        beer = Drink(drink_name="Beer", drink_price=3.5)
        db.session.add_all([cola, water, beer])
        db.session.commit()

    if not Dessert.query.first():
        tiramisu = Dessert(dessert_name="Tiramisu", dessert_price=4.0)
        icecream = Dessert(dessert_name="Ice Cream", dessert_price=3.0)
        db.session.add_all([tiramisu, icecream])
        db.session.commit()

    if not Customer.query.first():
        john = Customer(
            first_name="John", last_name="Doe",
            email="john@example.com", phone_number="123456789",
            birthdate=date(1990, 5, 20), address="123 Main St", postal_code="1000"
        )
        jane = Customer(
            first_name="Jane", last_name="Smith",
            email="jane@example.com", phone_number="987654321",
            birthdate=date(1985, 7, 15), address="456 Elm St", postal_code="2000"
        )
        db.session.add_all([john, jane])
        db.session.commit()

    if not DeliveryPerson.query.first():
        dp1 = DeliveryPerson(first_name="Alice", last_name="Rider", phone_number="5551234", postal_code="1000")
        dp2 = DeliveryPerson(first_name="Bob", last_name="Courier", phone_number="5555678", postal_code="2000")
        db.session.add_all([dp1, dp2])
        db.session.commit()

    if not DiscountCode.query.first():
        summer = DiscountCode(
            code="SUMMER10",
            discount_percentage=10.0,
            expires_at=datetime.utcnow() + timedelta(days=30),
            is_used=False
        )
        db.session.add(summer)
        db.session.commit()

    if not Order.query.first():
        john = Customer.query.filter_by(email="john@example.com").first()
        dp1 = DeliveryPerson.query.filter_by(postal_code="1000").first()
        summer = DiscountCode.query.filter_by(code="SUMMER10").first()
        margherita = Pizza.query.filter_by(pizza_name="Margherita").first()
        cola = Drink.query.filter_by(drink_name="Cola").first()

        order1 = Order(customer=john, delivery_person=dp1, discount=summer, status="Delivered")
        order1.pizzas.append(margherita)
        order1.drinks.append(cola)
        db.session.add(order1)
        db.session.commit()

        payment1 = Payment(order_id=order1.id, amount=order1.total_amount, payment_date=datetime.utcnow())
        db.session.add(payment1)
        db.session.commit()


def create_app():
    app = Flask(__name__)


    load_dotenv()

    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost:3306/pizza"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()
        seed_db()

    @app.route('/')
    def home():
        return "Flask app with SQLAlchemy is running!"

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

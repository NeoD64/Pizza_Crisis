import random
from datetime import date, datetime, timedelta, timezone
from faker import Faker
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from Model import (
    db, Customer, DiscountCode, DeliveryPerson, Order,
    Pizza, Ingredient, Drink, Dessert, Payment, OrderPizza, OrderDessert, OrderDrink, GenderEnum
)


fake = Faker('nl_BE')


def seed_database():

    print("Database seeding")
    if Customer.query.first():
        print("Database already contains data. Seeding skipped.")
        return

    session = db.session

    # seed base data
    _seed_ingredients(session)
    _seed_pizzas_and_link_ingredients(session)
    _seed_drinks(session)
    _seed_desserts(session)
    _seed_discount_codes(session)
    # seed customers

    customers = _seed_customers(session, count=30)
    _seed_staff(session)
    delivery_personnel = _seed_delivery_personnel(session, count=20)

    # seed order
    _seed_orders_and_payments(session, customers, delivery_personnel, count=100)

    print("Database seeding complete!")




def _seed_ingredients(session: Session):
    ingredients = [
        Ingredient(ingredient_name="Cheese", ingredient_price=1.0),
        Ingredient(ingredient_name="Tomato Sauce", ingredient_price=0.5),
        Ingredient(ingredient_name="Pepperoni", ingredient_price=1.5),
        Ingredient(ingredient_name="Mushrooms", ingredient_price=1.2),
        Ingredient(ingredient_name="Onion", ingredient_price=0.8),
        Ingredient(ingredient_name="Olives", ingredient_price=1.0),
        Ingredient(ingredient_name="Vegan Cheese", ingredient_price=1.8),
        Ingredient(ingredient_name="Pineapple", ingredient_price=1.0),
        Ingredient(ingredient_name="Chicken", ingredient_price=2.0),
    ]
    session.add_all(ingredients)
    session.commit()


def _seed_pizzas_and_link_ingredients(session: Session):
    pizzas_data = {
        "Margherita": {"base_price": 5.00, "category": "Vegetarian", "ingredients": ["Cheese", "Tomato Sauce"]},
        "Pepperoni": {"base_price": 6.00, "category": "Normal", "ingredients": ["Cheese", "Tomato Sauce", "Pepperoni"]},
        "Veggie": {"base_price": 6.50, "category": "Vegetarian",
                   "ingredients": ["Cheese", "Tomato Sauce", "Mushrooms", "Onion", "Olives"]},
        "Hawaiian": {"base_price": 7.00, "category": "Normal",
                     "ingredients": ["Cheese", "Tomato Sauce", "Pineapple", "Chicken"]},
        "BBQ Chicken": {"base_price": 7.50, "category": "Normal",
                        "ingredients": ["Cheese", "Tomato Sauce", "Chicken", "Onion"]},
        "Vegan Delight": {"base_price": 6.50, "category": "Vegan",
                          "ingredients": ["Vegan Cheese", "Tomato Sauce", "Mushrooms", "Olives"]},
    }

    pizzas_to_add = [Pizza(pizza_name=name, base_price=data['base_price'], category=data['category']) for name, data in
                     pizzas_data.items()]
    session.add_all(pizzas_to_add)
    session.commit()

    for pizza in pizzas_to_add:
        ingredient_names = pizzas_data[pizza.pizza_name]['ingredients']
        ingredients_to_link = session.query(Ingredient).filter(Ingredient.ingredient_name.in_(ingredient_names)).all()
        pizza.ingredients.extend(ingredients_to_link)
    session.commit()


def _seed_drinks(session: Session):
    drinks = [Drink(drink_name="Cola", drink_price=2.5), Drink(drink_name="Water", drink_price=1.0),
              Drink(drink_name="Beer", drink_price=3.5)]
    session.add_all(drinks)
    session.commit()


def _seed_desserts(session: Session):
    desserts = [Dessert(dessert_name="Tiramisu", dessert_price=4.0),
                Dessert(dessert_name="Ice Cream", dessert_price=3.0)]
    session.add_all(desserts)
    session.commit()


def _seed_discount_codes(session: Session):
    codes = [
        DiscountCode(code="SUMMER10", discount_percentage=10.0,
                     expires_at=datetime.now(timezone.utc) + timedelta(days=30), is_used=False),
        DiscountCode(code="WELCOME20", discount_percentage=20.0,
                     expires_at=datetime.now(timezone.utc) + timedelta(days=90), is_used=False),
    ]
    session.add_all(codes)
    session.commit()


def _seed_customers(session: Session, count=20) -> list[Customer]:
    customers = []
    for _ in range(count):
        profile = fake.profile()
        customer = Customer(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone_number=fake.unique.phone_number(),
            birthdate=profile['birthdate'],
            address=fake.street_address(),
            postal_code=fake.postcode(),
            password_hash=generate_password_hash("password123", method='pbkdf2:sha256'),
            gender = random.choice(list(GenderEnum))
        )
        customers.append(customer)
    session.add_all(customers)
    session.commit()
    return customers


def _seed_staff(session: Session):
    staff_members = [
        Customer(first_name="Néo", last_name="Deward", phone_number="0495208229", birthdate=date(2006, 10, 28),
                 address="Admin HQ", postal_code="666",
                 password_hash=generate_password_hash("Osenroastery", method='pbkdf2:sha256'), is_staff=True),
        Customer(first_name="Moaaz", last_name="BRO", phone_number="0987654321", birthdate=date(1969, 6, 7),
                 address="Admin HQ", postal_code="9999",
                 password_hash=generate_password_hash("TomPepels", method='pbkdf2:sha256'), is_staff=True),
    ]
    session.add_all(staff_members)
    session.commit()


def _seed_delivery_personnel(session: Session, count=5) -> list[DeliveryPerson]:
    personnel = []
    for _ in range(count):
        person = DeliveryPerson(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            phone_number=fake.unique.phone_number(),
            postal_code=fake.postcode(),
            available_at=datetime.now(timezone.utc) #  all are available
        )
        personnel.append(person)
    session.add_all(personnel)
    session.commit()
    return personnel


def _seed_orders_and_payments(session: Session, customers: list[Customer], delivery_personnel: list[DeliveryPerson],
                              count=100):
    pizzas = Pizza.query.all()
    drinks = Drink.query.all()
    desserts = Dessert.query.all()

    available_driver_pool = list(delivery_personnel)

    orders_to_add = []
    for _ in range(count):
        customer = random.choice(customers)

        status = random.choices(
            ["DELIVERED", "OUT_FOR_DELIVERY", "PENDING_ASSIGNMENT"],
            weights=[0.9, 0.05, 0.05],
            k=1
        )[0]
        order_date = None
        estimated_delivery_time = None
        delivery_person = None


        if status == "PENDING_ASSIGNMENT":
            minutes_ago = random.randint(31, 60)
            order_date = datetime.utcnow() - timedelta(minutes=minutes_ago)

        elif status == "OUT_FOR_DELIVERY":
            minutes_ago = random.randint(1, 30)
            order_date = datetime.utcnow() - timedelta(minutes=minutes_ago)
            estimated_delivery_time = order_date + timedelta(minutes=30)

            if available_driver_pool:
                driver_index = random.randrange(len(available_driver_pool))
                delivery_person = available_driver_pool.pop(driver_index)
            else:
                status = "PENDING_ASSIGNMENT"
                minutes_ago = random.randint(31, 60)
                order_date = datetime.utcnow() - timedelta(minutes=minutes_ago)
                estimated_delivery_time = None  # Reset this

        if status == "DELIVERED":

            if order_date is None:
                is_recent = random.choices([True, False], weights=[0.75, 0.25], k=1)[0]
                days_past = random.randint(0, 29) if is_recent else random.randint(30, 90)
                order_date = datetime.utcnow() - timedelta(days=days_past, hours=random.randint(1, 23))

            delivery_person = random.choice(delivery_personnel)


        new_order = Order(
            customer=customer,
            delivery_person=delivery_person,
            status=status,
            order_date=order_date,
            estimated_delivery_time=estimated_delivery_time
        )


        items_in_order = {'pizzas': {}, 'drinks': {}, 'desserts': {}}
        for _ in range(random.randint(2, 5)):
            item_type = random.choices(['pizza', 'drink', 'dessert'], weights=[0.7, 0.2, 0.1], k=1)[0]
            if item_type == 'pizza' and pizzas:
                chosen = random.choice(pizzas)
                items_in_order['pizzas'][chosen] = items_in_order['pizzas'].get(chosen, 0) + 1
            elif item_type == 'drink' and drinks:
                chosen = random.choice(drinks)
                items_in_order['drinks'][chosen] = items_in_order['drinks'].get(chosen, 0) + 1
            elif item_type == 'dessert' and desserts:
                chosen = random.choice(desserts)
                items_in_order['desserts'][chosen] = items_in_order['desserts'].get(chosen, 0) + 1

        for pizza_obj, qty in items_in_order['pizzas'].items():
            new_order.pizzas.append(OrderPizza(pizza=pizza_obj, quantity=qty))
        for drink_obj, qty in items_in_order['drinks'].items():
            new_order.drinks.append(OrderDrink(drink=drink_obj, quantity=qty))
        for dessert_obj, qty in items_in_order['desserts'].items():
            new_order.desserts.append(OrderDessert(dessert=dessert_obj, quantity=qty))

        if new_order.pizzas or new_order.drinks or new_order.desserts:
            orders_to_add.append(new_order)

    session.add_all(orders_to_add)
    session.flush()

    payments = [Payment(order_id=order.id, amount=order.total_amount, payment_date=order.order_date) for order in
                orders_to_add]
    session.add_all(payments)
    session.commit()
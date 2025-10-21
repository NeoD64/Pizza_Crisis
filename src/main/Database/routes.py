from flask import render_template, Blueprint, session, redirect, url_for, request, flash
from Model import (
    Pizza, Dessert, Drink, Order, db, Customer, DeliveryPerson, OrderPizza, OrderDessert,
    OrderDrink, Payment  # <-- Import Payment
)
from DiscountAndLoyaltyManager import DiscountAndLoyaltyManager
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import joinedload
from functools import wraps
from sqlalchemy import func, desc

bp = Blueprint("main", __name__)


def get_basket():
    """basket in dict form"""
    basket = session.get("basket", {"pizzas": {}, "drinks": {}, "desserts": {}})
    for key in ["pizzas", "drinks", "desserts"]:
        if isinstance(basket.get(key), list): # Handle legacy list format if any
            new_map = {}
            for item_id in basket[key]:
                new_map[str(item_id)] = new_map.get(str(item_id), 0) + 1
            basket[key] = new_map
    session["basket"] = basket
    return basket

def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('main.login'))
        return view_func(*args, **kwargs)
    return wrapper

@bp.route("/")
def home():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    return render_template("home.html")

@bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        phone_number = request.form["phone_number"]
        birthdate_str = request.form["birthdate"]
        address = request.form["address"]
        postal_code = request.form["postal_code"]
        password = request.form["password"]

        birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d").date()

        # Check if phone number already exists
        if Customer.query.filter_by(phone_number=phone_number).first():
            flash("Phone number already registered. Please log in or use a different number.", "danger")
            return render_template("register.html")

        new_customer = Customer(
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            birthdate=birthdate,
            address=address,
            postal_code=postal_code
        )
        new_customer.set_password(password)

        try:
            db.session.add(new_customer)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("main.login"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred during registration: {e}", "danger")
            return render_template("register.html")
    return render_template("register.html")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        phone_number = request.form["phone_number"]
        password = request.form["password"]

        customer = Customer.query.filter_by(phone_number=phone_number).first()

        if customer and customer.check_password(password):
            session["user_id"] = customer.id
            flash("Logged in successfully!", "success")
            return redirect(url_for("main.home"))
        else:
            flash("Invalid phone number or password.", "danger")
    return render_template("login.html")

@bp.route("/logout")
def logout():
    session.pop("user_id", None)

    flash("You have been logged out.", "info")
    return redirect(url_for("main.login"))


@bp.route("/menu", methods=["GET", "POST"])
@login_required
def menu():
    pizzas = Pizza.query.all()
    desserts = Dessert.query.all()
    drinks = Drink.query.all()

    basket = get_basket()
    basket_items = []
    subtotal = 0.0
    current_customer_id = session.get('user_id')
    customer = Customer.query.get(current_customer_id)


    for item_type, items_in_basket in basket.items():
        if item_type == "pizzas":
            for pid, qty in items_in_basket.items():
                pizza = Pizza.query.get(int(pid))
                if pizza:
                    price = pizza.final_amount() * qty
                    basket_items.append({
                        "id": pid, "type": "pizzas",
                        "name": pizza.pizza_name,
                        "qty": qty,
                        "price": price,
                        "category": pizza.category
                    })
                    subtotal += price
        elif item_type == "drinks":
            for did, qty in items_in_basket.items():
                drink = Drink.query.get(int(did))
                if drink:
                    price = drink.drink_price * qty
                    basket_items.append({
                        "id": did, "type": "drinks",
                        "name": drink.drink_name,
                        "qty": qty,
                        "price": price
                    })
                    subtotal += price
        elif item_type == "desserts":
            for desid, qty in items_in_basket.items():
                dessert = Dessert.query.get(int(desid))
                if dessert:
                    price = dessert.dessert_price * qty
                    basket_items.append({
                        "id": desid, "type": "desserts",
                        "name": dessert.dessert_name,
                        "qty": qty,
                        "price": price
                    })
                    subtotal += price

    discount_code_input = request.form.get("discount_code")
    final_total = subtotal
    applied_discounts = []
    invalid_code = False

    if customer:
        temp_order_for_discounts = Order(customer_id=customer.id)

        for item_data in basket_items:
            qty = item_data["qty"]

            if item_data["type"] == "pizzas":
                pizza = Pizza.query.get(int(item_data["id"]))
                if pizza:
                    temp_order_for_discounts.pizzas.append(
                        OrderPizza(pizza=pizza, quantity=qty)
                    )

            elif item_data["type"] == "drinks":
                drink = Drink.query.get(int(item_data["id"]))
                if drink:
                    temp_order_for_discounts.drinks.append(
                        OrderDrink(drink=drink, quantity=qty)
                    )

            elif item_data["type"] == "desserts":
                dessert = Dessert.query.get(int(item_data["id"]))
                if dessert:
                    temp_order_for_discounts.desserts.append(
                        OrderDessert(dessert=dessert, quantity=qty)
                    )

        manager = DiscountAndLoyaltyManager(customer, temp_order_for_discounts, discount_code_input)
        final_total, applied_discounts = manager.apply_all_discounts(db.session)
        invalid_code = manager.invalid_code

    else:
        flash("Customer not found for discount calculation. Please log in.", "danger")

    return render_template(
        "menu.html",
        pizzas=pizzas,
        desserts=desserts,
        drinks=drinks,
        basket_items=basket_items,
        subtotal=subtotal,
        final_total=final_total,
        discounts=applied_discounts,
        invalid_code=invalid_code,
        logged_in_customer=customer
    )


@bp.route("/add_to_basket/<item_type>/<int:item_id>", methods=["GET"])
@login_required
def add_to_basket(item_type, item_id):
    basket = get_basket()
    key = str(item_id)
    basket[item_type][key] = basket[item_type].get(key, 0) + 1
    session["basket"] = basket
    flash(f"Item added to basket!", "success")
    return redirect(url_for("main.menu"))


@bp.route("/remove_from_basket/<item_type>/<int:item_id>", methods=["GET"])
@login_required
def remove_from_basket(item_type, item_id):
    basket = get_basket()
    key = str(item_id)
    if key in basket[item_type]:
        basket[item_type][key] -= 1
        if basket[item_type][key] <= 0:
            del basket[item_type][key]
        flash(f"Item removed from basket.", "info")
    session["basket"] = basket
    return redirect(url_for("main.menu"))


@bp.route("/checkout", methods=["POST"])
@login_required
def checkout():
    customer_id = session.get("user_id")
    if not customer_id:
        flash("Please log in to complete your order.", "danger")
        return redirect(url_for("main.login"))

    basket = get_basket()
    if not (basket["pizzas"] or basket["drinks"] or basket["desserts"]):
        flash("Your basket is empty! Add some items before checking out.", "warning")
        return redirect(url_for("main.menu"))

    customer = Customer.query.get(customer_id)
    if not customer:
        flash("Customer not found. Please log in again.", "danger")
        session.pop("user_id", None)
        return redirect(url_for("main.login"))

    discount_code_input = request.form.get("discount_code")

    new_order = Order(customer=customer)
    db.session.add(new_order)


    try:

        db.session.flush()

        for pid, qty in basket["pizzas"].items():
            pizza = Pizza.query.get(int(pid))
            if pizza:
                order_pizza_assoc = OrderPizza(pizza=pizza, quantity=qty)
                new_order.pizzas.append(order_pizza_assoc)
            else:
                raise ValueError(f"Pizza with ID {pid} not found.")

        for did, qty in basket["drinks"].items():
            drink = Drink.query.get(int(did))
            if drink:
                order_drink_assoc = OrderDrink(drink=drink, quantity=qty)
                new_order.drinks.append(order_drink_assoc)
            else:
                raise ValueError(f"Drink with ID {did} not found.")

        for desid, qty in basket["desserts"].items():
            dessert = Dessert.query.get(int(desid))
            if dessert:
                order_dessert_assoc = OrderDessert( dessert=dessert, quantity=qty)
                new_order.desserts.append(order_dessert_assoc)
            else:
                raise ValueError(f"Dessert with ID {desid} not found.")


        manager = DiscountAndLoyaltyManager(customer, new_order, discount_code_input)
        final_total, applied_discounts = manager.apply_all_discounts(db.session)


        new_payment = Payment(order_id=new_order.id, amount=final_total)
        db.session.add(new_payment)


        available_delivery_person = DeliveryPerson.query.filter(
            DeliveryPerson.postal_code == customer.postal_code,
            DeliveryPerson.available_at <= datetime.utcnow()
        ).order_by(DeliveryPerson.available_at.asc()).first()

        if available_delivery_person:
            new_order.delivery_person = available_delivery_person
            new_order.status = "OUT_FOR_DELIVERY"
            available_delivery_person.available_at = datetime.utcnow() + timedelta(minutes=30)
            new_order.estimated_delivery_time = datetime.utcnow() + timedelta(minutes=30)
            flash(f"Order placed successfully! Delivery assigned to {available_delivery_person.first_name}.", "success")
        else:
            new_order.status = "PENDING_ASSIGNMENT"
            new_order.estimated_delivery_time = datetime.utcnow() + timedelta(minutes=60)
            flash("Order placed, but no delivery person is immediately available. Expect slight delay.", "warning")

        db.session.commit()
        session.pop("basket", None)
        session["last_order_id"] = new_order.id
        return redirect(url_for("main.confirmation"))

    except Exception as e:
        db.session.rollback()
        flash(f"Error placing order: {e}", "danger")
        return redirect(url_for("main.menu"))


@bp.route("/cancel_order/<int:order_id>", methods=["POST"])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)

    if order.customer_id != session.get('user_id'):
        flash("You do not have permission to cancel this order.", "danger")
        return redirect(url_for('main.home'))

    cancellation_window = timedelta(minutes=5)


    if datetime.utcnow() > order.order_date + cancellation_window:
        flash("The 5-minute cancellation window has passed.", "warning")
        return redirect(url_for('main.confirmation'))

    if order.status not in ["PENDING", "PENDING_ASSIGNMENT"]:
        flash("This order can no longer be cancelled as it is already being processed.", "warning")
        return redirect(url_for('main.confirmation'))

    order.status = "CANCELLED"
    db.session.commit()
    flash("Your order has been successfully cancelled.", "success")

    return redirect(url_for('main.confirmation'))

@bp.route("/confirmation")
@login_required
def confirmation():
    order_id = session.get("last_order_id")
    if not order_id:
        flash("No recent order found to confirm.", "warning")
        return redirect(url_for("main.home"))


    order = Order.query.options(
        joinedload(Order.customer),
        joinedload(Order.delivery_person),
        joinedload(Order.discount),
        joinedload(Order.pizzas),
        joinedload(Order.drinks),
        joinedload(Order.desserts)
    ).get(order_id)

    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for("main.home"))

    is_cancellable = False
    cancellation_window = timedelta(minutes=5)
    if order.status in ["PENDING", "PENDING_ASSIGNMENT"] and datetime.utcnow() < order.order_date + cancellation_window:
        is_cancellable = True

    pizza_items_with_qty = []
    for assoc in order.pizzas:
        pizza_items_with_qty.append({'pizza': assoc.pizza, 'quantity': assoc.quantity, 'price': assoc.pizza.final_amount() * assoc.quantity})

    drink_items_with_qty = []
    for assoc in order.drinks:
        drink_items_with_qty.append({'drink': assoc.drink, 'quantity': assoc.quantity, 'price': assoc.drink.drink_price * assoc.quantity})

    dessert_items_with_qty = []
    for assoc in order.desserts:
        dessert_items_with_qty.append({'dessert': assoc.dessert, 'quantity': assoc.quantity, 'price': assoc.dessert.dessert_price * assoc.quantity})


    return render_template(
        "confirmation.html",
        order=order,
        pizza_items_with_qty=pizza_items_with_qty,
        drink_items_with_qty=drink_items_with_qty,
        dessert_items_with_qty=dessert_items_with_qty,
        delivery_person=order.delivery_person,
        estimated_delivery_time=order.estimated_delivery_time.strftime("%H:%M") if order.estimated_delivery_time else "N/A",
        is_cancellable = is_cancellable
    )

@bp.route("/staff_reports")
@login_required
def staff_reports():
    customer_id = session.get('user_id')
    customer = Customer.query.get(customer_id)

    #staff only
    if not customer or not customer.is_staff:
        flash("Access denied. Staff members only.", "danger")
        return redirect(url_for("main.home"))

    timespan_filter = request.args.get('timespan', 'month')
    gender_filter = request.args.get('gender', 'all')
    age_group_filter = request.args.get('age_group', 'all')
    postal_code_filter = request.args.get('postal_code', 'all')

    earnings_query = db.session.query(
        Customer.postal_code,
        func.sum(Payment.amount).label("total_earnings")
    ).join(Order, Customer.id == Order.customer_id).join(Payment, Order.id == Payment.order_id)

    earnings_query = earnings_query.filter(Order.status == "DELIVERED")

    today = datetime.utcnow().date()
    if timespan_filter == 'week':
        start_date = today - timedelta(days=today.weekday())
        earnings_query = earnings_query.filter(Order.order_date >= start_date)
    elif timespan_filter == 'month':
        start_date = today.replace(day=1)
        earnings_query = earnings_query.filter(Order.order_date >= start_date)

    if gender_filter and gender_filter != 'all':
        earnings_query = earnings_query.filter(Customer.gender == gender_filter)

    if postal_code_filter and postal_code_filter != 'all':
        earnings_query = earnings_query.filter(Customer.postal_code == postal_code_filter)

    if age_group_filter and age_group_filter != 'all':

        age = func.timestampdiff(func.year(), Customer.birthdate, func.curdate())
        if age_group_filter == '18-25':
            earnings_query = earnings_query.filter(age.between(18, 25))
        elif age_group_filter == '26-40':
            earnings_query = earnings_query.filter(age.between(26, 40))
        elif age_group_filter == '41-60':
            earnings_query = earnings_query.filter(age.between(41, 60))
        elif age_group_filter == '60+':
            earnings_query = earnings_query.filter(age >= 60)

    earnings_by_postal_code = earnings_query.group_by(Customer.postal_code).order_by(Customer.postal_code).all()
    # Undelivered Orders
    undelivered_orders = (
        Order.query
        .filter(Order.status != "DELIVERED")
        .options(joinedload(Order.customer), joinedload(Order.delivery_person))
        .all()
    )

    # Top 3 pizzas sold in the past month
    one_month_ago = datetime.utcnow() - timedelta(days=30)
    top_pizzas = (
        db.session.query(
            Pizza.pizza_name,
            func.sum(OrderPizza.quantity).label("total_quantity_sold")
        )
        .join(OrderPizza, Pizza.id == OrderPizza.pizza_id)
        .join(Order, Order.id == OrderPizza.order_id)
        .filter(Order.order_date >= one_month_ago, Order.status == "DELIVERED")
        .group_by(Pizza.pizza_name)
        .order_by(desc("total_quantity_sold"))
        .limit(3)
        .all()
    )

    all_postal_codes = db.session.query(Customer.postal_code).distinct().order_by(Customer.postal_code).all()
    all_postal_codes = [pc[0] for pc in all_postal_codes]

    return render_template(
        "staff_reports.html",
        undelivered_orders=undelivered_orders,
        top_pizzas=top_pizzas,
        earnings_by_postal_code=earnings_by_postal_code,
        current_timespan=timespan_filter,
        current_gender=gender_filter,
        current_age_group=age_group_filter,
        current_postal_code=postal_code_filter,
        all_postal_codes=all_postal_codes
    )
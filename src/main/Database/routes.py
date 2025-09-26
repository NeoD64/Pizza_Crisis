from flask import render_template, Blueprint, session, redirect, url_for, request
from Model import Pizza, Dessert, Drink, Order, db, Customer
from DiscountAndLoyaltyManager import DiscountAndLoyaltyManager

bp = Blueprint("main", __name__)


def get_basket():
    """Ensure basket always in {type: {id: qty}} dict format."""
    basket = session.get("basket", {"pizzas": {}, "drinks": {}, "desserts": {}})
    for key in ["pizzas", "drinks", "desserts"]:
        if isinstance(basket.get(key), list):
            new_map = {}
            for item_id in basket[key]:
                new_map[str(item_id)] = new_map.get(str(item_id), 0) + 1
            basket[key] = new_map
    session["basket"] = basket
    return basket


@bp.route("/")
def home():
    return render_template("home.html")


@bp.route("/menu", methods=["GET", "POST"])
def menu():
    pizzas = Pizza.query.all()
    desserts = Dessert.query.all()
    drinks = Drink.query.all()

    basket = get_basket()
    basket_items = []
    subtotal = 0.0

    for pid, qty in basket["pizzas"].items():
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


    for did, qty in basket["drinks"].items():
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

    for desid, qty in basket["desserts"].items():
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

    discount_code = None
    if request.method == "POST":
        discount_code = request.form.get("discount_code")

    customer = Customer.query.get(1)
    temp_order = Order(customer_id=1)
    db.session.add(temp_order)
    db.session.flush()

    for item in basket_items:
        if item["type"] == "pizzas":
            temp_order.pizzas.append(Pizza.query.get(int(item["id"])))
        elif item["type"] == "drinks":
            temp_order.drinks.append(Drink.query.get(int(item["id"])))
        elif item["type"] == "desserts":
            temp_order.desserts.append(Dessert.query.get(int(item["id"])))

    manager = DiscountAndLoyaltyManager(customer, temp_order, discount_code)
    final_total, discounts = manager.apply_all_discounts(db.session)

    db.session.rollback()

    return render_template(
        "menu.html",
        pizzas=pizzas,
        desserts=desserts,
        drinks=drinks,
        basket_items=basket_items,
        subtotal=subtotal,
        final_total=final_total,
        discounts=discounts,
        invalid_code=manager.invalid_code
    )


@bp.route("/add_to_basket/<item_type>/<int:item_id>", methods=["GET"])
def add_to_basket(item_type, item_id):
    basket = get_basket()
    key = str(item_id)
    basket[item_type][key] = basket[item_type].get(key, 0) + 1
    session["basket"] = basket
    return redirect(url_for("main.menu"))


@bp.route("/remove_from_basket/<item_type>/<int:item_id>", methods=["GET"])
def remove_from_basket(item_type, item_id):
    basket = get_basket()
    key = str(item_id)
    if key in basket[item_type]:
        basket[item_type][key] -= 1
        if basket[item_type][key] <= 0:
            del basket[item_type][key]
    session["basket"] = basket
    return redirect(url_for("main.menu"))


@bp.route("/checkout")
def checkout():
    basket = get_basket()
    if not (basket["pizzas"] or basket["drinks"] or basket["desserts"]):
        return redirect(url_for("main.menu"))

    order = Order(customer_id=1)
    db.session.add(order)
    db.session.flush()

    for pid, qty in basket["pizzas"].items():
        pizza = Pizza.query.get(int(pid))
        if pizza:
            for _ in range(qty):
                order.pizzas.append(pizza)

    for did, qty in basket["drinks"].items():
        drink = Drink.query.get(int(did))
        if drink:
            for _ in range(qty):
                order.drinks.append(drink)

    for desid, qty in basket["desserts"].items():
        dessert = Dessert.query.get(int(desid))
        if dessert:
            for _ in range(qty):
                order.desserts.append(dessert)

    db.session.commit()
    session.pop("basket", None)

    return redirect(url_for("main.order"))


@bp.route("/order")
def order():
    return render_template("order.html")


@bp.route("/reports")
def reports():
    return render_template("reports.html")

from flask import render_template, Blueprint, session, redirect, url_for, request
from Model import Pizza, Dessert, Drink, Order, db, Customer
from DiscountAndLoyaltyManager import DiscountAndLoyaltyManager
import re

bp = Blueprint("main", __name__)

def get_basket():
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
        form_code = request.form.get("discount_code", "").strip()
        discount_code = form_code if form_code else None
        session["discount_code"] = discount_code
    else:
        discount_code = session.get("discount_code") if basket_items else None

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

    discounts = []
    invalid_code = False
    final_total = subtotal

    if discount_code:
        manager = DiscountAndLoyaltyManager(customer, temp_order, discount_code)
        final_total, discounts, invalid_code = manager.apply_all_discounts(db.session)
        db.session.rollback()

        if invalid_code:
            final_total = subtotal
        elif not discounts:
            final_total = subtotal
            discounts = []

        else:
            pct = None
            for d in discounts:
                if "%" in d and "❌" not in d:
                    match = re.search(r"(\d+)", d)
                    if match:
                        pct = int(match.group(1))
                        break

            if pct is not None:
                final_total = subtotal * (1 - pct / 100)
            elif any("Free Pizza" in d for d in discounts):
                pizzas_in_basket = [
                    Pizza.query.get(int(pid)) for pid in basket["pizzas"].keys()
                ]
                cheapest = min(
                    (p.final_amount() for p in pizzas_in_basket if p), default=0
                )
                final_total = subtotal - cheapest
            else:
                final_total = subtotal
    else:
        manager = DiscountAndLoyaltyManager(customer, temp_order, None)
        final_total, discounts, _ = manager.apply_all_discounts(db.session)
        db.session.rollback()
        if not discounts:
            final_total = subtotal

    final_total = round(final_total, 2)

    if invalid_code or not basket_items:
        session.pop("discount_code", None)

    return render_template(
        "menu.html",
        pizzas=pizzas,
        desserts=desserts,
        drinks=drinks,
        basket_items=basket_items,
        subtotal=subtotal,
        final_total=final_total,
        discounts=discounts,
        invalid_code=invalid_code
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

    discount_code = session.get("discount_code")
    customer = Customer.query.get(1)

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

    manager = DiscountAndLoyaltyManager(customer, order, discount_code)
    final_total, discounts, invalid_code = manager.apply_all_discounts(db.session, for_checkout=True)

    db.session.commit()

    session.pop("basket", None)
    session.pop("discount_code", None)
    return redirect(url_for("main.menu"))



@bp.route("/reports")
def reports():
    return render_template("reports.html")

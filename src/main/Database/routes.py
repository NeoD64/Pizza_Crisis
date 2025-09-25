from flask import render_template, Blueprint
from Model import Pizza

bp = Blueprint("main", __name__)

@bp.route("/")
def home():
    return render_template("home.html")

@bp.route("/menu")
def menu():
    pizzas = Pizza.query.all()

    pizza_data = []
    for pizza in pizzas:
        pizza_data.append({
            "name": pizza.pizza_name,
            "price": pizza.final_amount()  # ✅ now always uses base_price
        })

    return render_template("menu.html", pizzas=pizza_data)


@bp.route("/order")
def order():
    return render_template("order.html")

@bp.route("/reports")
def reports():
    return render_template("reports.html")

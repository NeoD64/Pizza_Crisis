from flask import render_template, Blueprint
from Model import Pizza, Dessert, Drink

bp = Blueprint("main", __name__)

@bp.route("/")
def home():
    return render_template("home.html")

@bp.route("/menu")

def menu():
    pizzas = Pizza.query.all()
    desserts = Dessert.query.all()
    drinks = Drink.query.all()
    return render_template("menu.html", pizzas=pizzas, desserts=desserts, drinks=drinks)


@bp.route("/order")
def order():
    return render_template("order.html")

@bp.route("/reports")
def reports():
    return render_template("reports.html")

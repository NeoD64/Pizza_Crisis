from flask import render_template, Blueprint

# Define a blueprint
bp = Blueprint("main", __name__)

@bp.route("/")
def home():
    return render_template("home.html")

@bp.route("/menu")
def menu():
    return render_template("menu.html")

@bp.route("/order")
def order():
    return render_template("order.html")

@bp.route("/reports")
def reports():
    return render_template("reports.html")

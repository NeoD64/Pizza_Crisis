import time
import threading
import os
from flask import Flask
from dotenv import load_dotenv
from datetime import datetime, timedelta

from Model import db, Order, DeliveryPerson
from routes import bp
from Seeding import seed_database


def create_app():

    app = Flask(__name__)
    load_dotenv()


    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "a-default-secret-key")
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST', 'localhost')}:3306/{os.getenv('DB_NAME', 'pizza')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()
        seed_database()

    @app.route('/ping')
    def ping():
        return "Flask app is running!"

    return app


def check_deliveries_job(app):

    with app.app_context():
        print("Scheduler: Checking delivery statuses...")
        now = datetime.utcnow()

        overdue_orders = Order.query.filter(
            Order.status == "OUT_FOR_DELIVERY",
            Order.estimated_delivery_time < now
        ).all()
        for order in overdue_orders:
            order.status = "DELIVERED"

        pending_orders = Order.query.filter_by(status="PENDING_ASSIGNMENT").all()
        for order in pending_orders:
            available_driver = DeliveryPerson.query.filter(
                DeliveryPerson.available_at <= now,
                DeliveryPerson.postal_code == order.customer.postal_code
            ).order_by(DeliveryPerson.available_at.asc()).first()
            if available_driver:
                order.delivery_person = available_driver
                order.status = "OUT_FOR_DELIVERY"
                order.estimated_delivery_time = now + timedelta(minutes=30)
                available_driver.available_at = order.estimated_delivery_time
                db.session.add(available_driver)

        db.session.commit()



def run_scheduler(app):
    while True:
        check_deliveries_job(app)
        time.sleep(300)  # Check every 5 minutes


if __name__ == '__main__':
    app = create_app()

    scheduler_thread = threading.Thread(target=run_scheduler, args=(app,), daemon=True)
    scheduler_thread.start()

    app.run(debug=True, use_reloader=False)
from flask import Flask
from Model import db
from dotenv import load_dotenv
import os

def create_app():
    app = Flask(__name__)

    # Loads environment variables from .env file
    load_dotenv()
    # Will use database connection from env file which is your password and username for MYSQL!
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@localhost:3306/pizza"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()

    @app.route('/')
    def home():
        return "Flask app with SQLAlchemy is running!"

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)

from flask import Flask
from model import db

def create_app():
    app = Flask(__name__)

    # Configure database connection
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:MYsql&$64@localhost:3306/pizza'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)

    # Register routes
    @app.route('/')
    def home():
        return "Flask app with SQLAlchemy is running!"

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
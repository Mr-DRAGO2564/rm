from flask import Flask, render_template, redirect, url_for, flash
import os
from extensions import db, bcrypt, login_manager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///orderhub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

from models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Default route
@app.route('/')
def home():
    from flask_login import current_user
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'supplier':
            return redirect(url_for('supplier.dashboard'))
        elif current_user.role == 'restaurant':
            return redirect(url_for('restaurant.products'))
    return redirect(url_for('auth.login'))

# Register Blueprints
from routes.auth import auth_bp
from routes.restaurant import restaurant_bp
from routes.supplier import supplier_bp
from routes.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(restaurant_bp)
app.register_blueprint(supplier_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)

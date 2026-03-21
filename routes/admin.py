from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import User, Order, Product

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def check_role():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return False
    return True

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not check_role(): return redirect(url_for('home'))
    
    users = User.query.all()
    orders = Order.query.order_by(Order.date_ordered.desc()).all()
    products = Product.query.all()
    
    return render_template('admin/dashboard.html', users=users, orders=orders, products=products)

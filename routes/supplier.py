from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Product, Order, OrderItem

supplier_bp = Blueprint('supplier', __name__, url_prefix='/supplier')

def check_role():
    if current_user.role != 'supplier':
        flash('Access denied.', 'danger')
        return False
    return True

@supplier_bp.route('/dashboard')
@login_required
def dashboard():
    if not check_role(): return redirect(url_for('home'))
    
    # Get all products belonging to this supplier
    my_products = Product.query.filter_by(supplier_id=current_user.id).all()
    my_product_ids = [p.id for p in my_products]
    
    if not my_product_ids:
        upcoming_orders = []
    else:
        # Get order items that include this supplier's products
        order_items = OrderItem.query.filter(OrderItem.product_id.in_(my_product_ids)).all()
        # Group by order
        order_ids = set([oi.order_id for oi in order_items])
        upcoming_orders = Order.query.filter(Order.id.in_(order_ids)).order_by(Order.date_ordered.desc()).all()
        
    return render_template('supplier/upcoming_orders.html', orders=upcoming_orders, my_products=my_products)

@supplier_bp.route('/product/add', methods=['POST'])
@login_required
def add_product():
    if not check_role(): return redirect(url_for('home'))
    
    name = request.form.get('name')
    description = request.form.get('description')
    price = float(request.form.get('price'))
    stock = int(request.form.get('stock'))
    
    new_product = Product(name=name, description=description, price=price, stock=stock, supplier_id=current_user.id)
    db.session.add(new_product)
    db.session.commit()
    flash('Product added successfully', 'success')
    return redirect(url_for('supplier.dashboard'))

@supplier_bp.route('/order/update_status/<int:order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    if not check_role(): return redirect(url_for('home'))
    
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status in ['Pending', 'Processed', 'Shipped', 'Delivered']:
        order.status = new_status
        db.session.commit()
        flash(f'Order #{order.id} status updated to {new_status}.', 'success')
        
    return redirect(url_for('supplier.dashboard'))

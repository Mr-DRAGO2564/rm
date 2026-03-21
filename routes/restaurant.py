from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from extensions import db
from models import Product, Order, OrderItem, CartItem

restaurant_bp = Blueprint('restaurant', __name__, url_prefix='/restaurant')

# Dependency function to check role
def check_role():
    if current_user.role != 'restaurant':
        flash('Access denied.', 'danger')
        return False
    return True

@restaurant_bp.route('/products')
@login_required
def products():
    if not check_role(): return redirect(url_for('home'))
    products = Product.query.filter(Product.stock > 0).all()
    return render_template('restaurant/products.html', products=products)

@restaurant_bp.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    if not check_role(): return redirect(url_for('home'))
    
    if request.method == 'POST':
        product_id = request.form.get('product_id')
        quantity = int(request.form.get('quantity', 1))
        
        # Check if already in cart
        item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if item:
            item.quantity += quantity
        else:
            new_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
            db.session.add(new_item)
        db.session.commit()
        flash('Added to cart.', 'success')
        return redirect(url_for('restaurant.products'))
        
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    
    # Calculate total and hydrate with product info
    total = 0
    items_with_product = []
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if product:
            subtotal = product.price * item.quantity
            total += subtotal
            items_with_product.append({'cart_item': item, 'product': product, 'subtotal': subtotal})
    
    return render_template('restaurant/cart.html', cart_items=items_with_product, total=total)

@restaurant_bp.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    if not check_role(): return redirect(url_for('home'))
    item = CartItem.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash('Item removed.', 'info')
    return redirect(url_for('restaurant.cart'))

@restaurant_bp.route('/checkout', methods=['GET'])
@login_required
def checkout():
    if not check_role(): return redirect(url_for('home'))
    
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('restaurant.products'))
        
    total_amount = sum(Product.query.get(item.product_id).price * item.quantity for item in cart_items if Product.query.get(item.product_id) and Product.query.get(item.product_id).stock >= item.quantity)
    
    if total_amount <= 0:
        flash('No valid items in cart.', 'warning')
        return redirect(url_for('restaurant.cart'))
        
    import qrcode
    import io
    import base64
    
    # Generate Mock UPI URI
    merchant_vpa = 'testmerchant@upi' 
    pay_uri = f"upi://pay?pa={merchant_vpa}&pn=OrderHub&am={total_amount:.2f}&cu=INR"
    
    # Generate QR Code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(pay_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    qr_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return render_template('restaurant/payment.html', total_amount=total_amount, qr_b64=qr_b64)

@restaurant_bp.route('/checkout/confirm', methods=['POST'])
@login_required
def checkout_confirm():
    if not check_role(): return redirect(url_for('home'))
    
    mobile_no = request.form.get('mobile_number')
    transaction_id = request.form.get('transaction_id')
    
    if not mobile_no:
        flash('Mobile number is required for payment confirmation.', 'danger')
        return redirect(url_for('restaurant.checkout'))
        
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        return redirect(url_for('restaurant.products'))
        
    total_amount = 0
    order_items_to_add = []
    
    for item in cart_items:
        product = Product.query.get(item.product_id)
        if product and product.stock >= item.quantity:
            cost = product.price * item.quantity
            total_amount += cost
            order_items_to_add.append(OrderItem(product_id=product.id, quantity=item.quantity, price=product.price))
            # Reduce stock
            product.stock -= item.quantity
            
    # Create order
    new_order = Order(
        user_id=current_user.id, 
        total_amount=total_amount, 
        status='Pending',
        payment_mobile_no=mobile_no,
        transaction_id=transaction_id
    )
    db.session.add(new_order)
    db.session.flush() # get order id
    
    for oi in order_items_to_add:
        oi.order_id = new_order.id
        db.session.add(oi)
        
    # Clear cart
    for item in cart_items:
        db.session.delete(item)
        
    db.session.commit()
    flash('Payment verified and Order placed successfully!', 'success')
    return redirect(url_for('restaurant.my_orders'))

@restaurant_bp.route('/orders')
@login_required
def my_orders():
    if not check_role(): return redirect(url_for('home'))
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.date_ordered.desc()).all()
    return render_template('restaurant/orders.html', orders=orders)

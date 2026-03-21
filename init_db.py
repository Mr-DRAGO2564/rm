from app import app
from extensions import db, bcrypt
from models import User, Product

with app.app_context():
    db.drop_all()
    db.create_all()

    # Create admin
    hashed_pw = bcrypt.generate_password_hash('admin').decode('utf-8')
    admin = User(username='admin', password=hashed_pw, role='admin')

    # Create supplier
    hashed_pw_sup = bcrypt.generate_password_hash('supplier').decode('utf-8')
    supplier1 = User(username='supplier1', password=hashed_pw_sup, role='supplier')

    # Create restaurant
    hashed_pw_res = bcrypt.generate_password_hash('restaurant').decode('utf-8')
    res1 = User(username='restaurant1', password=hashed_pw_res, role='restaurant')

    db.session.add_all([admin, supplier1, res1])
    db.session.commit()

    # Create some products for supplier1
    p1 = Product(name='Fresh Tomatoes', description='Box of 10kg fresh tomatoes', price=25.0, stock=50, supplier_id=supplier1.id)
    p2 = Product(name='Wagyu Beef', description='Premium A5 Wagyu beef per kg', price=150.0, stock=10, supplier_id=supplier1.id)
    p3 = Product(name='Olive Oil', description='Extra virgin olive oil 5L bottle', price=45.0, stock=30, supplier_id=supplier1.id)
    
    db.session.add_all([p1, p2, p3])
    db.session.commit()

    print("Database seeded successfully with test accounts.")
    print("Admin: admin / admin")
    print("Supplier: supplier1 / supplier")
    print("Restaurant: restaurant1 / restaurant")

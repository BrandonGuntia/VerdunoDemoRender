#!/usr/bin/env python3
"""
測試數據生成腳本
用於在重置數據庫後快速創建測試數據
"""

from app import app, db
from models import Product, Customer, Admin, Invoice, OrderItem
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def create_test_products():
    """創建測試產品"""
    print("\n📦 Creating test products...")
    
    products = [
        {
            'id': 'AMGSL',
            'name': 'AMG Sirloin Whole',
            'price': 19.99,
            'subclass': 'Beef'
        },
        {
            'id': 'AMGSL250',
            'name': 'AMG Sirloin 250g',
            'price': 21.99,
            'subclass': 'Beef'
        },
        {
            'id': 'JCMB2SL',
            'name': 'JC MB2 Sirloin Whole',
            'price': 28,
            'subclass': 'Beef'
        },
        {
            'id': 'JCMB4SL',
            'name': 'JC MB4 Sirloin Whole',
            'price': 35,
            'subclass': 'Beef'
        },
        {
            'id': 'CHICKEN10',
            'name': 'Chicken Size 10',
            'price': 7,
            'subclass': 'Chicken'
        },
        {
            'id': 'CHICKEN16',
            'name': 'Chicken Size 16',
            'price': 9,
            'subclass': 'Chicken'
        },
        {
            'id': 'CHICKENT',
            'name': 'Chicken Thigh',
            'price': 14.99,
            'subclass': 'Chicken'
        },
        {
            'id': 'CHICKENB',
            'name': 'Chicken Breast',
            'price': 9.99,
            'subclass': 'Chicken'
        },
        {
            'id': 'WBD',
            'name': 'Wagyu Diced',
            'price': 22.4,
            'subclass': 'Beef'
        },
        {
            'id': 'WBM',
            'name': 'Wagyu Mince',
            'price': 12,
            'subclass': 'Beef'
        }
    ]
    
    created_count = 0
    for product_data in products:
        # 檢查產品是否已存在
        existing = Product.query.get(product_data['id'])
        if existing:
            print(f"  ⚠️  Product {product_data['id']} already exists, skipping...")
            continue
        
        product = Product(
            id=product_data['id'],
            name=product_data['name'],
            price=product_data['price'],
            subclass=product_data['subclass']
        )
        db.session.add(product)
        created_count += 1
        print(f"  ✅ Created product: {product_data['id']} - {product_data['name']}")
    
    db.session.commit()
    print(f"\n✨ Successfully created {created_count} products!")
    return created_count

def create_test_customers():
    """創建測試客戶"""
    print("\n👥 Creating test customers...")
    
    customers = [
        {
            'name': 'Kago',
            'email': 'Kago@Verduno.com',
            'password': 'Kago1234',
            'special_item_ids': ['AMGSL', 'AMGSL250']
        },
        {
            'name': 'Ben',
            'email': 'Ben@Verduno.com',
            'password': 'Ben1234',
            'special_item_ids': ['WBD', 'CHICKENB']
        },
        {
            'name': 'Ko',
            'email': 'Ko@Verduno.com',
            'password': 'Ko123',
            'special_item_ids': ['CHICKEN16', 'WBM']
        },
        {
            'name': 'Kamal',
            'email': 'Kamal@Verduno.com',
            'password': 'Kamal23',
            'special_item_ids': []
        }
    ]
    
    created_count = 0
    for customer_data in customers:
        # 檢查客戶是否已存在
        existing = Customer.query.filter_by(email=customer_data['email']).first()
        if existing:
            print(f"  ⚠️  Customer {customer_data['email']} already exists, skipping...")
            continue
        
        customer = Customer(
            name=customer_data['name'],
            email=customer_data['email']
        )
        # 設置密碼（會自動加密）
        customer.password = generate_password_hash(customer_data['password'])
        
        # 設置特殊產品 ID
        customer.set_special_items(customer_data['special_item_ids'])
        
        db.session.add(customer)
        created_count += 1
        print(f"  ✅ Created customer: {customer_data['name']} ({customer_data['email']})")
    
    db.session.commit()
    print(f"\n✨ Successfully created {created_count} customers!")
    return created_count

def create_admin_account():
    """創建管理員帳號"""
    print("\n🔑 Creating admin account...")
    
    # 檢查是否已存在 admin
    existing_admin = Admin.query.filter_by(username='admin').first()
    if existing_admin:
        print("  ⚠️  Admin account already exists, skipping...")
        return 0
    
    admin = Admin(
        username='admin',
        email='admin@example.com',
        is_super_admin=True
    )
    admin.set_password('admin123')
    
    db.session.add(admin)
    db.session.commit()
    
    print("  ✅ Created admin account")
    print("     Username: admin")
    print("     Password: admin123")
    print("     ⚠️  Please change the password in production!")
    return 1

def create_test_invoices():
    """創建測試發票和訂單項目"""
    print("\n🧾 Creating test invoices and order items...")
    
    # 獲取客戶
    kago = Customer.query.filter_by(email='Kago@Verduno.com').first()
    ben = Customer.query.filter_by(email='Ben@Verduno.com').first()
    ko = Customer.query.filter_by(email='Ko@Verduno.com').first()
    kamal = Customer.query.filter_by(email='Kamal@Verduno.com').first()
    
    if not all([kago, ben, ko, kamal]):
        print("  ⚠️  Not all customers exist, skipping invoice creation...")
        return 0
    
    # 獲取產品
    products = {p.id: p for p in Product.query.all()}
    
    if not products:
        print("  ⚠️  No products exist, skipping invoice creation...")
        return 0
    
    today = datetime.now().date()
    
    invoices_data = [
        # Day 1 訂單 (5張)
        {
            'invoice_number': 'INV-2025-001',
            'customer': kago,
            'delivery_date': today + timedelta(days=1),
            'status': 'Pending',
            'items': [
                {'product_id': 'AMGSL', 'quantity': 5},
                {'product_id': 'AMGSL250', 'quantity': 10},
                {'product_id': 'CHICKEN10', 'quantity': 3},
            ]
        },
        {
            'invoice_number': 'INV-2025-002',
            'customer': ben,
            'delivery_date': today + timedelta(days=1),
            'status': 'Pending',
            'items': [
                {'product_id': 'WBD', 'quantity': 8},
                {'product_id': 'CHICKENB', 'quantity': 15},
                {'product_id': 'JCMB2SL', 'quantity': 4},
            ]
        },
        {
            'invoice_number': 'INV-2025-003',
            'customer': ko,
            'delivery_date': today + timedelta(days=1),
            'status': 'Pending',
            'items': [
                {'product_id': 'CHICKEN16', 'quantity': 20},
                {'product_id': 'WBM', 'quantity': 12},
                {'product_id': 'CHICKENT', 'quantity': 6},
            ]
        },
        {
            'invoice_number': 'INV-2025-004',
            'customer': kamal,
            'delivery_date': today + timedelta(days=1),
            'status': 'Pending',
            'items': [
                {'product_id': 'JCMB4SL', 'quantity': 3},
                {'product_id': 'CHICKEN10', 'quantity': 10},
                {'product_id': 'WBD', 'quantity': 5},
            ]
        },
        {
            'invoice_number': 'INV-2025-005',
            'customer': kago,
            'delivery_date': today + timedelta(days=1),
            'status': 'Completed',
            'items': [
                {'product_id': 'AMGSL', 'quantity': 8},
                {'product_id': 'WBM', 'quantity': 10},
                {'product_id': 'CHICKENT', 'quantity': 5},
            ]
        },
        
        # Day 2 訂單 (6張)
        {
            'invoice_number': 'INV-2025-006',
            'customer': ben,
            'delivery_date': today + timedelta(days=2),
            'status': 'Pending',
            'items': [
                {'product_id': 'CHICKENB', 'quantity': 25},
                {'product_id': 'CHICKEN16', 'quantity': 15},
            ]
        },
        {
            'invoice_number': 'INV-2025-007',
            'customer': ko,
            'delivery_date': today + timedelta(days=2),
            'status': 'Pending',
            'items': [
                {'product_id': 'WBD', 'quantity': 12},
                {'product_id': 'JCMB4SL', 'quantity': 6},
                {'product_id': 'AMGSL250', 'quantity': 8},
            ]
        },
        {
            'invoice_number': 'INV-2025-008',
            'customer': kamal,
            'delivery_date': today + timedelta(days=2),
            'status': 'Completed',
            'items': [
                {'product_id': 'CHICKEN10', 'quantity': 30},
                {'product_id': 'CHICKENT', 'quantity': 10},
            ]
        },
        {
            'invoice_number': 'INV-2025-009',
            'customer': kago,
            'delivery_date': today + timedelta(days=2),
            'status': 'Pending',
            'items': [
                {'product_id': 'AMGSL', 'quantity': 15},
                {'product_id': 'JCMB2SL', 'quantity': 7},
            ]
        },
        {
            'invoice_number': 'INV-2025-010',
            'customer': ben,
            'delivery_date': today + timedelta(days=2),
            'status': 'Pending',
            'items': [
                {'product_id': 'WBM', 'quantity': 20},
                {'product_id': 'CHICKENB', 'quantity': 12},
                {'product_id': 'CHICKEN16', 'quantity': 8},
            ]
        },
        {
            'invoice_number': 'INV-2025-011',
            'customer': ko,
            'delivery_date': today + timedelta(days=2),
            'status': 'Cancelled',
            'items': [
                {'product_id': 'JCMB4SL', 'quantity': 2},
            ]
        },
        
        # Day 3 訂單 (7張)
        {
            'invoice_number': 'INV-2025-012',
            'customer': kamal,
            'delivery_date': today + timedelta(days=3),
            'status': 'Pending',
            'items': [
                {'product_id': 'CHICKEN10', 'quantity': 18},
                {'product_id': 'CHICKEN16', 'quantity': 22},
                {'product_id': 'CHICKENT', 'quantity': 14},
            ]
        },
        {
            'invoice_number': 'INV-2025-013',
            'customer': kago,
            'delivery_date': today + timedelta(days=3),
            'status': 'Pending',
            'items': [
                {'product_id': 'AMGSL', 'quantity': 10},
                {'product_id': 'AMGSL250', 'quantity': 20},
            ]
        },
        {
            'invoice_number': 'INV-2025-014',
            'customer': ben,
            'delivery_date': today + timedelta(days=3),
            'status': 'Completed',
            'items': [
                {'product_id': 'WBD', 'quantity': 15},
                {'product_id': 'WBM', 'quantity': 18},
                {'product_id': 'JCMB2SL', 'quantity': 5},
            ]
        },
        {
            'invoice_number': 'INV-2025-015',
            'customer': ko,
            'delivery_date': today + timedelta(days=3),
            'status': 'Pending',
            'items': [
                {'product_id': 'CHICKENB', 'quantity': 30},
                {'product_id': 'CHICKEN16', 'quantity': 25},
            ]
        },
        {
            'invoice_number': 'INV-2025-016',
            'customer': kamal,
            'delivery_date': today + timedelta(days=3),
            'status': 'Pending',
            'items': [
                {'product_id': 'JCMB4SL', 'quantity': 8},
                {'product_id': 'AMGSL', 'quantity': 6},
            ]
        },
        {
            'invoice_number': 'INV-2025-017',
            'customer': kago,
            'delivery_date': today + timedelta(days=3),
            'status': 'Pending',
            'items': [
                {'product_id': 'WBD', 'quantity': 10},
                {'product_id': 'CHICKENT', 'quantity': 12},
                {'product_id': 'CHICKEN10', 'quantity': 15},
            ]
        },
        {
            'invoice_number': 'INV-2025-018',
            'customer': ben,
            'delivery_date': today + timedelta(days=3),
            'status': 'Completed',
            'items': [
                {'product_id': 'JCMB2SL', 'quantity': 9},
                {'product_id': 'WBM', 'quantity': 16},
            ]
        },
        
        # Day 4 訂單 (8張)
        {
            'invoice_number': 'INV-2025-019',
            'customer': ko,
            'delivery_date': today + timedelta(days=4),
            'status': 'Pending',
            'items': [
                {'product_id': 'CHICKEN16', 'quantity': 35},
                {'product_id': 'CHICKENB', 'quantity': 20},
            ]
        },
        {
            'invoice_number': 'INV-2025-020',
            'customer': kamal,
            'delivery_date': today + timedelta(days=4),
            'status': 'Pending',
            'items': [
                {'product_id': 'AMGSL250', 'quantity': 12},
                {'product_id': 'JCMB4SL', 'quantity': 5},
                {'product_id': 'WBD', 'quantity': 8},
            ]
        },
        {
            'invoice_number': 'INV-2025-021',
            'customer': kago,
            'delivery_date': today + timedelta(days=4),
            'status': 'Pending',
            'items': [
                {'product_id': 'AMGSL', 'quantity': 20},
                {'product_id': 'CHICKEN10', 'quantity': 10},
            ]
        },
        {
            'invoice_number': 'INV-2025-022',
            'customer': ben,
            'delivery_date': today + timedelta(days=4),
            'status': 'Completed',
            'items': [
                {'product_id': 'CHICKENB', 'quantity': 18},
                {'product_id': 'WBM', 'quantity': 22},
                {'product_id': 'CHICKENT', 'quantity': 8},
            ]
        },
        {
            'invoice_number': 'INV-2025-023',
            'customer': ko,
            'delivery_date': today + timedelta(days=4),
            'status': 'Pending',
            'items': [
                {'product_id': 'JCMB2SL', 'quantity': 10},
                {'product_id': 'WBD', 'quantity': 14},
            ]
        },
        {
            'invoice_number': 'INV-2025-024',
            'customer': kamal,
            'delivery_date': today + timedelta(days=4),
            'status': 'Cancelled',
            'items': [
                {'product_id': 'CHICKEN16', 'quantity': 5},
            ]
        },
        {
            'invoice_number': 'INV-2025-025',
            'customer': kago,
            'delivery_date': today + timedelta(days=4),
            'status': 'Pending',
            'items': [
                {'product_id': 'AMGSL', 'quantity': 12},
                {'product_id': 'AMGSL250', 'quantity': 15},
                {'product_id': 'WBM', 'quantity': 10},
            ]
        },
        {
            'invoice_number': 'INV-2025-026',
            'customer': ben,
            'delivery_date': today + timedelta(days=4),
            'status': 'Pending',
            'items': [
                {'product_id': 'JCMB4SL', 'quantity': 7},
                {'product_id': 'CHICKENB', 'quantity': 25},
                {'product_id': 'CHICKEN10', 'quantity': 20},
            ]
        },
    ]
    
    created_count = 0
    for invoice_data in invoices_data:
        # 檢查發票是否已存在
        existing = Invoice.query.filter_by(invoice_number=invoice_data['invoice_number']).first()
        if existing:
            print(f"  ⚠️  Invoice {invoice_data['invoice_number']} already exists, skipping...")
            continue
        
        # 創建發票
        invoice = Invoice(
            invoice_number=invoice_data['invoice_number'],
            customer_id=invoice_data['customer'].id,
            delivery_date=invoice_data['delivery_date'],
            status=invoice_data['status']
        )
        db.session.add(invoice)
        db.session.flush()  # 獲取 invoice.id
        
        # 創建訂單項目
        total_amount = 0
        for item_data in invoice_data['items']:
            product = products.get(item_data['product_id'])
            if not product:
                print(f"    ⚠️  Product {item_data['product_id']} not found, skipping...")
                continue
            
            quantity = item_data['quantity']
            unit_price = product.price
            total_price = quantity * unit_price
            
            order_item = OrderItem(
                invoice_id=invoice.id,
                product_id=product.id,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price
            )
            db.session.add(order_item)
            total_amount += total_price
        
        # 更新發票總金額
        invoice.total_amount = total_amount
        
        created_count += 1
        print(f"  ✅ Created invoice: {invoice_data['invoice_number']} for {invoice_data['customer'].name} (${total_amount:.2f})")
    
    db.session.commit()
    print(f"\n✨ Successfully created {created_count} invoices!")
    return created_count

def display_summary():
    """顯示數據庫摘要"""
    print("\n" + "="*60)
    print("📊 DATABASE SUMMARY")
    print("="*60)
    
    product_count = Product.query.count()
    customer_count = Customer.query.count()
    admin_count = Admin.query.count()
    invoice_count = Invoice.query.count()
    order_item_count = OrderItem.query.count()
    
    print(f"\n📦 Products: {product_count}")
    if product_count > 0:
        products = Product.query.all()
        for p in products:
            print(f"   - {p.id}: {p.name} (${p.price})")
    
    print(f"\n👥 Customers: {customer_count}")
    if customer_count > 0:
        customers = Customer.query.all()
        for c in customers:
            special_count = len(c.get_special_items())
            print(f"   - {c.name} ({c.email}) - {special_count} special items")
    
    print(f"\n🔑 Admins: {admin_count}")
    if admin_count > 0:
        admins = Admin.query.all()
        for a in admins:
            print(f"   - {a.username} ({a.email})")
    
    print(f"\n🧾 Invoices: {invoice_count}")
    if invoice_count > 0:
        invoices = Invoice.query.all()
        for inv in invoices:
            print(f"   - {inv.invoice_number}: {inv.customer.name} - ${inv.total_amount:.2f} ({inv.status})")
    
    print(f"\n📋 Order Items: {order_item_count}")
    
    print("\n" + "="*60)

def seed_all_data():
    """執行所有數據生成"""
    print("\n" + "="*60)
    print("🌱 SEEDING TEST DATA")
    print("="*60)
    
    with app.app_context():
        try:
            # 創建管理員
            admin_count = create_admin_account()
            
            # 創建產品
            product_count = create_test_products()
            
            # 創建客戶
            customer_count = create_test_customers()
            
            # 創建發票和訂單項目
            invoice_count = create_test_invoices()
            
            # 顯示摘要
            display_summary()
            
            print("\n✅ All test data created successfully!")
            print(f"   - {admin_count} admin(s)")
            print(f"   - {product_count} product(s)")
            print(f"   - {customer_count} customer(s)")
            print(f"   - {invoice_count} invoice(s)")
            
            print("\n" + "="*60)
            print("🚀 QUICK START GUIDE")
            print("="*60)
            print("\n1. Start the application:")
            print("   python app.py")
            print("\n2. Login credentials:")
            print("   Admin: admin / admin123")
            print("   Customer: Kago@Verduno.com / Kago1234")
            print("   Customer: Ben@Verduno.com / Ben1234")
            print("   Customer: Ko@Verduno.com / Ko123")
            print("   Customer: Kamal@Verduno.com / Kamal23")
            print("\n3. Access the application:")
            print("   http://localhost:8000")
            print("\n" + "="*60)
            
        except Exception as e:
            print(f"\n❌ Error creating test data: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    seed_all_data()
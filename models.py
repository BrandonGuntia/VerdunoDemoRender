from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Product(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    subclass = db.Column(db.String(50), nullable=False)
    
    def __repr__(self):
        return f'<Product {self.name}>'

class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    special_item_ids = db.Column(db.String(2000), default='[]')
    
    def get_special_items(self):
        return json.loads(self.special_item_ids) if self.special_item_ids else []
    
    def set_special_items(self, items):
        if len(items) > 99:
            items = items[:99]
        self.special_item_ids = json.dumps(items)
    
    def __repr__(self):
        return f'<Customer {self.name}>'

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    
    def __repr__(self):
        return f'<Message from {self.user}>'

class Order(db.Model):
    __tablename__ = 'orders'  # 重要：指定表名為 'orders' 而不是 'order'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    product_id = db.Column(db.String(50), db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_date = db.Column(db.Date, nullable=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    
    # 關聯
    customer = db.relationship('Customer', backref='orders')
    product = db.relationship('Product', backref='orders')
    
    def __repr__(self):
        return f'<Order {self.invoice_number}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else 'Unknown',
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Unknown',
            'product_price': self.product.price if self.product else 0,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'order_date': self.order_date.strftime('%Y-%m-%d %H:%M:%S'),
            'delivery_date': self.delivery_date.strftime('%Y-%m-%d') if self.delivery_date else None,
            'invoice_number': self.invoice_number,
            'status': self.status
        }
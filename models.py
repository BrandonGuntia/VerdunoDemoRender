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

class Invoice(db.Model):
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    delivery_date = db.Column(db.Date, nullable=False)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')  # Pending, Completed, Cancelled
    total_amount = db.Column(db.Float, default=0.0)
    
    # 關聯
    customer = db.relationship('Customer', backref='invoices')
    order_items = db.relationship('OrderItem', backref='invoice', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'
    
    def calculate_total(self):
        """計算發票總金額"""
        self.total_amount = sum(item.total_price for item in self.order_items)
        return self.total_amount
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_number': self.invoice_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer.name if self.customer else 'Unknown',
            'customer_email': self.customer.email if self.customer else '',
            'delivery_date': self.delivery_date.strftime('%Y-%m-%d'),
            'created_date': self.created_date.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'total_amount': self.total_amount,
            'items_count': len(self.order_items),
            'items': [item.to_dict() for item in self.order_items]
        }

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.String(50), db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    
    # 關聯
    product = db.relationship('Product', backref='order_items')
    
    def __repr__(self):
        return f'<OrderItem {self.product_id} x {self.quantity}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Unknown',
            'product_subclass': self.product.subclass if self.product else '',
            'quantity': self.quantity,
            'unit_price': self.unit_price,
            'total_price': self.total_price
        }
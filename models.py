from flask_sqlalchemy import SQLAlchemy
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
    name = db.Column(db.String(120), nullable=False)  # 改為 name
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    special_item_ids = db.Column(db.String(2000), default='[]')  # 存儲 JSON 數組，最多 99 個
    
    def get_special_items(self):
        """獲取特殊產品 ID 列表"""
        return json.loads(self.special_item_ids) if self.special_item_ids else []
    
    def set_special_items(self, items):
        """設置特殊產品 ID 列表（最多 99 個）"""
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
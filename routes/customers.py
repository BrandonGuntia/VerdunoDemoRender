from flask import Blueprint, request, jsonify
from models import db, Customer
from werkzeug.security import generate_password_hash
import json

customers_bp = Blueprint("customers", __name__)

@customers_bp.route("/", methods=["GET"])
def get_customers():
    limit = request.args.get('limit', type=int)
    search = request.args.get('search', type=str)
    
    query = Customer.query
    
    # 如果有搜索參數，按 ID 或 Name 搜索
    if search:
        search_pattern = f"%{search}%"
        # 對於 ID，嘗試轉換為整數搜索
        try:
            search_id = int(search)
            query = query.filter(
                db.or_(
                    Customer.id == search_id,
                    Customer.name.like(search_pattern)
                )
            )
        except ValueError:
            # 如果不是數字，只按名稱搜索
            query = query.filter(Customer.name.like(search_pattern))
    
    if limit:
        customers = query.limit(limit).all()
    else:
        customers = query.all()
    
    return jsonify([{
        "id": c.id,
        "name": c.name,
        "email": c.email,
        "special_item_ids": c.get_special_items()
    } for c in customers])

@customers_bp.route("/<int:customer_id>", methods=["GET"])
def get_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    return jsonify({
        "id": customer.id,
        "name": customer.name,
        "email": customer.email,
        "special_item_ids": customer.get_special_items()
    })

@customers_bp.route("/", methods=["POST"])
def add_customer():
    data = request.json
    
    # 驗證必填欄位
    if not data.get("name") or not data.get("password") or not data.get("email"):
        return jsonify({"message": "名稱、密碼和電子郵件都是必填的！"}), 400
    
    # 檢查電子郵件是否已存在
    existing_customer = Customer.query.filter_by(email=data["email"]).first()
    if existing_customer:
        return jsonify({"message": "電子郵件已存在！"}), 400
    
    # 處理特殊產品 ID
    special_items = data.get("special_item_ids", [])
    if len(special_items) > 99:
        return jsonify({"message": "特殊產品 ID 數量不能超過 99 個！"}), 400
    
    # 密碼加密
    hashed_password = generate_password_hash(data["password"])
    
    new_customer = Customer(
        name=data["name"],
        password=hashed_password,
        email=data["email"]
    )
    new_customer.set_special_items(special_items)
    
    db.session.add(new_customer)
    db.session.commit()
    
    return jsonify({"message": "Customer added!", "id": new_customer.id}), 201

@customers_bp.route("/<int:customer_id>", methods=["PUT"])
def update_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    data = request.json
    
    if "name" in data:
        customer.name = data["name"]
    
    if "email" in data:
        # 檢查新電子郵件是否已被其他用戶使用
        existing = Customer.query.filter(
            Customer.email == data["email"],
            Customer.id != customer_id
        ).first()
        if existing:
            return jsonify({"message": "電子郵件已被使用！"}), 400
        customer.email = data["email"]
    
    if "password" in data and data["password"]:
        customer.password = generate_password_hash(data["password"])
    
    if "special_item_ids" in data:
        special_items = data["special_item_ids"]
        if len(special_items) > 99:
            return jsonify({"message": "特殊產品 ID 數量不能超過 99 個！"}), 400
        customer.set_special_items(special_items)
    
    db.session.commit()
    
    return jsonify({"message": "Customer updated!"})

@customers_bp.route("/<int:customer_id>", methods=["DELETE"])
def delete_customer(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    db.session.delete(customer)
    db.session.commit()
    
    return jsonify({"message": "Customer deleted!"})
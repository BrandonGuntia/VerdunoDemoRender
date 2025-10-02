from flask import Blueprint, request, jsonify
from models import db, Product

products_bp = Blueprint("products", __name__)

@products_bp.route("/", methods=["GET"])
def get_products():
    limit = request.args.get('limit', type=int)
    search = request.args.get('search', type=str)
    
    query = Product.query
    
    # 如果有搜索參數，按 ID 或 Name 搜索
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Product.id.like(search_pattern),
                Product.name.like(search_pattern)
            )
        )
    
    if limit:
        products = query.limit(limit).all()
    else:
        products = query.all()
    
    return jsonify([{
        "id": p.id, 
        "name": p.name, 
        "price": p.price,
        "subclass": p.subclass
    } for p in products])

@products_bp.route("/<string:product_id>", methods=["GET"])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify({
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "subclass": product.subclass
    })

@products_bp.route("/", methods=["POST"])
def add_product():
    data = request.json
    
    # 驗證必填欄位
    if not data.get("id") or not data.get("name") or not data.get("price") or not data.get("subclass"):
        return jsonify({"message": "所有欄位都是必填的！"}), 400
    
    # 檢查 ID 是否已存在
    existing_product = Product.query.get(data["id"])
    if existing_product:
        return jsonify({"message": "產品 ID 已存在！"}), 400
    
    new_product = Product(
        id=data["id"],
        name=data["name"], 
        price=float(data["price"]),
        subclass=data["subclass"]
    )
    
    db.session.add(new_product)
    db.session.commit()
    
    return jsonify({"message": "Product added!", "id": data["id"]}), 201

@products_bp.route("/<string:product_id>", methods=["PUT"])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.json
    
    if "name" in data:
        product.name = data["name"]
    if "price" in data:
        product.price = float(data["price"])
    if "subclass" in data:
        product.subclass = data["subclass"]
    
    db.session.commit()
    
    return jsonify({"message": "Product updated!"})

@products_bp.route("/<string:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    
    return jsonify({"message": "Product deleted!"})
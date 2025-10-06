from flask import Blueprint, request, jsonify, session
from models import db, Customer, Admin
from werkzeug.security import check_password_hash

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["POST"])
def login():
    """統一登入端點"""
    data = request.json
    
    if not data.get('username') or not data.get('password'):
        return jsonify({"message": "Username and password are required!"}), 400
    
    username = data['username']
    password = data['password']
    
    # 首先檢查是否是 Admin
    admin = Admin.query.filter_by(username=username).first()
    if admin and admin.check_password(password):
        session['user_id'] = admin.id
        session['user_type'] = 'admin'
        session['username'] = admin.username
        return jsonify({
            "message": "Login successful!",
            "user_type": "admin",
            "username": admin.username
        }), 200
    
    # 如果不是 Admin，檢查是否是 Customer
    customer = Customer.query.filter_by(name=username).first()
    if customer and check_password_hash(customer.password, password):
        session['user_id'] = customer.id
        session['user_type'] = 'customer'
        session['username'] = customer.name
        return jsonify({
            "message": "Login successful!",
            "user_type": "customer",
            "username": customer.name
        }), 200
    
    return jsonify({"message": "Invalid username or password!"}), 401

@auth_bp.route("/logout", methods=["POST"])
def logout():
    """登出"""
    session.clear()
    return jsonify({"message": "Logout successful!"}), 200

@auth_bp.route("/check-session", methods=["GET"])
def check_session():
    """檢查當前登入狀態"""
    if 'user_id' in session:
        return jsonify({
            "logged_in": True,
            "user_type": session.get('user_type'),
            "username": session.get('username')
        }), 200
    return jsonify({"logged_in": False}), 200

@auth_bp.route("/create-admin", methods=["POST"])
def create_admin():
    """創建管理員帳號（僅用於初始化）"""
    data = request.json
    
    # 檢查是否已存在 Admin
    existing_admin = Admin.query.filter_by(username=data['username']).first()
    if existing_admin:
        return jsonify({"message": "Admin already exists!"}), 400
    
    new_admin = Admin(
        username=data['username'],
        email=data['email'],
        is_super_admin=data.get('is_super_admin', False)
    )
    new_admin.set_password(data['password'])
    
    db.session.add(new_admin)
    db.session.commit()
    
    return jsonify({"message": "Admin created successfully!"}), 201
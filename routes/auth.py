from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Customer

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    hashed_pw = generate_password_hash(data["password"], method="sha256")
    new_user = Customer(username=data["username"], email=data["email"], password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "User registered!"}), 201

@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    user = Customer.query.filter_by(username=data["username"]).first()
    if user and check_password_hash(user.password, data["password"]):
        session["user_id"] = user.id
        return jsonify({"message": "Login successful!"})
    return jsonify({"message": "Invalid credentials"}), 401

@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "Logged out"})

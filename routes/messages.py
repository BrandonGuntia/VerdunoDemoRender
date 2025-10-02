from flask import Blueprint, request, jsonify
from models import db, Message

messages_bp = Blueprint("messages", __name__)

@messages_bp.route("/", methods=["GET"])
def get_messages():
    messages = Message.query.all()
    return jsonify([{"id": m.id, "user": m.user, "content": m.content} for m in messages])

@messages_bp.route("/", methods=["POST"])
def add_message():
    data = request.json
    new_msg = Message(user=data["user"], content=data["content"])
    db.session.add(new_msg)
    db.session.commit()
    return jsonify({"message": "Message added!"}), 201

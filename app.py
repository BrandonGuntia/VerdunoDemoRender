from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import os

# =====================
# App Config
# =====================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# =====================
# Models
# =====================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    items = db.relationship("UserItem", backref="owner", lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False)

class UserItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey("item.id"), nullable=False)
    custom_price = db.Column(db.Float, nullable=True)
    item = db.relationship("Item", backref="user_items")

# =====================
# Flask-Login
# =====================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =====================
# Routes
# =====================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash("登入成功！", "success")
            if user.is_admin:
                return redirect(url_for("admin_page"))
            else:
                return redirect(url_for("home_page"))
        else:
            flash("帳號或密碼錯誤！", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("你已登出。", "info")
    return redirect(url_for("login"))

@app.route("/home")
@login_required
def home_page():
    if current_user.is_admin:
        return redirect(url_for("admin_page"))
    user_items = UserItem.query.filter_by(user_id=current_user.id).all()
    return render_template("home.html", user=current_user, user_items=user_items)

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin_page():
    if not current_user.is_admin:
        flash("你沒有權限進入 Admin 頁面！", "danger")
        return redirect(url_for("home_page"))

    users = User.query.all()
    items = Item.query.all()
    user_items = UserItem.query.all()

    if request.method == "POST":
        action = request.form.get("action")

        # 新增客戶帳號
        if action == "add_customer":
            username = request.form.get("username")
            password = request.form.get("password")
            hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
            new_user = User(username=username, password=hashed_pw, is_admin=False)
            db.session.add(new_user)
            db.session.commit()
            flash("新增客戶帳號成功！", "success")
            return redirect(url_for("admin_page"))

        # 刪除客戶帳號
        if action == "delete_customer":
            user_id = request.form.get("user_id")
            user = User.query.get(user_id)
            if user and not user.is_admin:
                db.session.delete(user)
                db.session.commit()
                flash("刪除客戶帳號成功！", "info")
            else:
                flash("無法刪除 Admin 帳號！", "danger")
            return redirect(url_for("admin_page"))

        # 新增客戶專屬產品
        if action == "add_user_item":
            user_id = request.form.get("user_id")
            item_id = request.form.get("item_id")
            custom_price = request.form.get("custom_price")
            if not custom_price:
                custom_price = None
            else:
                custom_price = float(custom_price)

            new_ui = UserItem(user_id=user_id, item_id=item_id, custom_price=custom_price)
            db.session.add(new_ui)
            db.session.commit()
            flash("新增客戶專屬產品成功！", "success")
            return redirect(url_for("admin_page"))

        # 刪除客戶專屬產品
        if action == "delete_user_item":
            ui_id = request.form.get("user_item_id")
            ui = UserItem.query.get(ui_id)
            if ui:
                db.session.delete(ui)
                db.session.commit()
                flash("刪除客戶專屬產品成功！", "info")
            return redirect(url_for("admin_page"))

    return render_template("admin.html", users=users, items=items, user_items=user_items)

# =====================
# Initialize DB & admin account
# =====================
def init_db():
    db.create_all()
    # 預設建立 admin 帳號
    if not User.query.filter_by(username="admin").first():
        hashed_pw = bcrypt.generate_password_hash("admin").decode("utf-8")
        admin_user = User(username="admin", password=hashed_pw, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()

# =====================
# Run App
# =====================
if __name__ == "__main__":
    with app.app_context():
        init_db()  # 初始化資料庫及 admin 帳號
    app.run(debug=True)

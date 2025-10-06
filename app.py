from flask import Flask, render_template, redirect, url_for, session
from flask_cors import CORS
from config import Config
from models import db
from routes.products import products_bp
from routes.customers import customers_bp
from routes.auth import auth_bp
from routes.messages import messages_bp
from routes.invoices import invoices_bp
import os
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
CORS(app, supports_credentials=True)

# 載入 API routes
app.register_blueprint(products_bp, url_prefix="/api/products")
app.register_blueprint(customers_bp, url_prefix="/api/customers")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(messages_bp, url_prefix="/api/messages")
app.register_blueprint(invoices_bp, url_prefix="/api/invoices")

# 裝飾器：要求登入
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# 裝飾器：要求 Admin 權限
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_type') != 'admin':
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# 公開頁面
@app.route("/")
def index():
    """首頁重定向到登入頁"""
    return redirect(url_for('login_page'))

@app.route("/login")
def login_page():
    """登入頁面"""
    return render_template("login.html")

@app.route("/register")
def register_page():
    """註冊頁面"""
    return render_template("register.html")

# Dashboard（登入後）
@app.route("/dashboard")
@login_required
def dashboard():
    """根據用戶類型顯示不同的 Dashboard"""
    if session.get('user_type') == 'admin':
        return render_template("dashboard.html")
    else:
        # 普通客戶直接跳轉到 testing-input
        return redirect(url_for('testing_input_page'))

# Admin 專用頁面
@app.route("/products")
@admin_required
def products_page():
    return render_template("products.html")

@app.route("/products/edit/<product_id>")
@admin_required
def product_edit_page(product_id):
    return render_template("product_edit.html")

@app.route("/customers")
@admin_required
def customers_page():
    return render_template("customers.html")

@app.route("/customers/edit/<int:customer_id>")
@admin_required
def customer_edit_page(customer_id):
    return render_template("customer_edit.html")

@app.route("/invoices")
@admin_required
def invoices_page():
    return render_template("invoices.html")

@app.route("/invoices/edit/<int:invoice_id>")
@admin_required
def invoice_edit_page(invoice_id):
    return render_template("invoice_edit.html")

@app.route("/cutting-list")
@admin_required
def cutting_list_page():
    return render_template("cutting_list.html")

@app.route("/cutting-list/<date>")
@admin_required
def cutting_list_edit_page(date):
    return render_template("cutting_list_edit.html")

# 所有用戶都可訪問的頁面
@app.route("/testing-input")
@login_required
def testing_input_page():
    return render_template("testing_input.html")

# 初始化數據庫
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
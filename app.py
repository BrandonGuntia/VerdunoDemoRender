from flask import Flask, render_template
from flask_cors import CORS
from config import Config
from models import db
from routes.products import products_bp
from routes.customers import customers_bp
from routes.auth import auth_bp
from routes.messages import messages_bp

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
CORS(app)

# 載入 API routes
app.register_blueprint(products_bp, url_prefix="/api/products")
app.register_blueprint(customers_bp, url_prefix="/api/customers")
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(messages_bp, url_prefix="/api/messages")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/products")
def products_page():
    return render_template("products.html")

@app.route("/products/edit/<product_id>")
def product_edit_page(product_id):
    return render_template("product_edit.html")

@app.route("/customers")
def customers_page():
    return render_template("customers.html")

@app.route("/customers/edit/<int:customer_id>")
def customer_edit_page(customer_id):
    return render_template("customer_edit.html")

@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/register")
def register_page():
    return render_template("register.html")




with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)

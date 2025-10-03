from flask import Blueprint, request, jsonify, send_file
from models import db, Order, Customer, Product
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

orders_bp = Blueprint("orders", __name__)

def generate_invoice_number():
    """生成唯一的發票編號 格式: INV-YYYYMMDD-XXXX"""
    today = datetime.now().strftime('%Y%m%d')
    # 找到今天最後一個訂單號
    last_order = Order.query.filter(
        Order.invoice_number.like(f'INV-{today}-%')
    ).order_by(Order.id.desc()).first()
    
    if last_order:
        last_num = int(last_order.invoice_number.split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    return f'INV-{today}-{new_num:04d}'

@orders_bp.route("/", methods=["GET"])
def get_orders():
    search = request.args.get('search', type=str)
    date = request.args.get('date', type=str)
    
    query = Order.query
    
    # 搜索功能
    if search:
        query = query.join(Customer).filter(
            db.or_(
                Order.invoice_number.like(f'%{search}%'),
                Customer.name.like(f'%{search}%')
            )
        )
    
    # 日期篩選
    if date:
        try:
            filter_date = datetime.strptime(date, '%Y-%m-%d').date()
            query = query.filter(db.func.date(Order.order_date) == filter_date)
        except ValueError:
            pass
    
    orders = query.order_by(Order.order_date.desc()).all()
    return jsonify([order.to_dict() for order in orders])

@orders_bp.route("/<int:order_id>", methods=["GET"])
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict())

@orders_bp.route("/", methods=["POST"])
def create_order():
    data = request.json
    
    # 驗證必填欄位
    if not data.get('customer_id') or not data.get('product_id') or not data.get('quantity'):
        return jsonify({"message": "客戶ID、產品ID和數量都是必填的！"}), 400
    
    # 驗證客戶存在
    customer = Customer.query.get(data['customer_id'])
    if not customer:
        return jsonify({"message": "客戶不存在！"}), 404
    
    # 驗證產品存在
    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({"message": "產品不存在！"}), 404
    
    # 計算總價
    quantity = int(data['quantity'])
    if quantity <= 0:
        return jsonify({"message": "數量必須大於0！"}), 400
    
    total_price = product.price * quantity
    
    # 生成發票號碼
    invoice_number = generate_invoice_number()
    
    # 處理送貨日期
    delivery_date = None
    if data.get('delivery_date'):
        try:
            delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"message": "送貨日期格式錯誤！"}), 400
    
    # 創建訂單
    new_order = Order(
        customer_id=data['customer_id'],
        product_id=data['product_id'],
        quantity=quantity,
        total_price=total_price,
        delivery_date=delivery_date,
        invoice_number=invoice_number,
        status=data.get('status', 'Pending')
    )
    
    db.session.add(new_order)
    db.session.commit()
    
    return jsonify({
        "message": "訂單創建成功！",
        "order": new_order.to_dict()
    }), 201

@orders_bp.route("/<int:order_id>", methods=["PUT"])
def update_order(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.json
    
    if 'quantity' in data:
        quantity = int(data['quantity'])
        if quantity <= 0:
            return jsonify({"message": "數量必須大於0！"}), 400
        order.quantity = quantity
        order.total_price = order.product.price * quantity
    
    if 'status' in data:
        order.status = data['status']
    
    if 'delivery_date' in data:
        if data['delivery_date']:
            try:
                order.delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({"message": "送貨日期格式錯誤！"}), 400
        else:
            order.delivery_date = None
    
    db.session.commit()
    
    return jsonify({"message": "訂單更新成功！", "order": order.to_dict()})

@orders_bp.route("/<int:order_id>", methods=["DELETE"])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    
    return jsonify({"message": "訂單刪除成功！"})

@orders_bp.route("/<int:order_id>/pdf", methods=["GET"])
def generate_invoice_pdf(order_id):
    order = Order.query.get_or_404(order_id)
    
    # 創建 PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # 標題
    title = Paragraph(f"<b>INVOICE</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # 發票信息
    invoice_info = [
        ['Invoice Number:', order.invoice_number],
        ['Order Date:', order.order_date.strftime('%Y-%m-%d %H:%M:%S')],
        ['Delivery Date:', order.delivery_date.strftime('%Y-%m-%d') if order.delivery_date else 'Not Set'],
        ['Status:', order.status]
    ]
    
    info_table = Table(invoice_info, colWidths=[2*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # 客戶信息
    customer_title = Paragraph("<b>Customer Information</b>", styles['Heading2'])
    elements.append(customer_title)
    customer_info = [
        ['Customer ID:', str(order.customer_id)],
        ['Customer Name:', order.customer.name],
        ['Email:', order.customer.email]
    ]
    
    customer_table = Table(customer_info, colWidths=[2*inch, 3*inch])
    customer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(customer_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # 訂單明細
    order_title = Paragraph("<b>Order Details</b>", styles['Heading2'])
    elements.append(order_title)
    
    data = [
        ['Product ID', 'Product Name', 'Unit Price', 'Quantity', 'Total'],
        [
            order.product_id,
            order.product.name,
            f'${order.product.price:.2f}',
            str(order.quantity),
            f'${order.total_price:.2f}'
        ]
    ]
    
    order_table = Table(data, colWidths=[1.5*inch, 2*inch, 1*inch, 1*inch, 1*inch])
    order_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(order_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # 總計
    total_data = [['Total Amount:', f'${order.total_price:.2f}']]
    total_table = Table(total_data, colWidths=[4.5*inch, 2*inch])
    total_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.black),
    ]))
    elements.append(total_table)
    
    # 生成 PDF
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'invoice_{order.invoice_number}.pdf',
        mimetype='application/pdf'
    )
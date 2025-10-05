from flask import Blueprint, request, jsonify, send_file
from models import db, Invoice, OrderItem, Customer, Product
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import inch

invoices_bp = Blueprint("invoices", __name__)

def generate_invoice_number():
    """生成唯一的發票編號 格式: INV-YYYYMMDD-XXXX"""
    today = datetime.now().strftime('%Y%m%d')
    last_invoice = Invoice.query.filter(
        Invoice.invoice_number.like(f'INV-{today}-%')
    ).order_by(Invoice.id.desc()).first()
    
    if last_invoice:
        last_num = int(last_invoice.invoice_number.split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    return f'INV-{today}-{new_num:04d}'

@invoices_bp.route("/", methods=["GET"])
def get_invoices():
    search = request.args.get('search', type=str)
    date = request.args.get('date', type=str)
    
    query = Invoice.query
    
    # 搜索功能
    if search:
        query = query.join(Customer).filter(
            db.or_(
                Invoice.invoice_number.like(f'%{search}%'),
                Customer.name.like(f'%{search}%')
            )
        )
    
    # 日期篩選（按送貨日期）
    if date:
        try:
            filter_date = datetime.strptime(date, '%Y-%m-%d').date()
            query = query.filter(Invoice.delivery_date == filter_date)
        except ValueError:
            pass
    
    invoices = query.order_by(Invoice.delivery_date.desc(), Invoice.created_date.desc()).all()
    return jsonify([invoice.to_dict() for invoice in invoices])

@invoices_bp.route("/<int:invoice_id>", methods=["GET"])
def get_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return jsonify(invoice.to_dict())

@invoices_bp.route("/create", methods=["POST"])
def create_invoice():
    """
    創建發票（可包含多個訂單項目）
    接收格式: {
        "customer_id": 1,
        "delivery_date": "2025-10-05",
        "items": [
            {"product_id": "PROD001", "quantity": 2},
            {"product_id": "PROD002", "quantity": 1}
        ]
    }
    """
    data = request.json
    
    # 驗證必填欄位
    if not data.get('customer_id') or not data.get('delivery_date') or not data.get('items'):
        return jsonify({"message": "Customer ID, delivery date, and order items are required!"}), 400
    
    # 驗證客戶存在
    customer = Customer.query.get(data['customer_id'])
    if not customer:
        return jsonify({"message": "Customer not found!"}), 404
    
    # 解析送貨日期
    try:
        delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"message": "Invalid delivery date format!"}), 400
    
    # 檢查是否已存在相同客戶、相同送貨日期的待處理發票
    existing_invoice = Invoice.query.filter_by(
        customer_id=data['customer_id'],
        delivery_date=delivery_date,
        status='Pending'
    ).first()
    
    # 驗證並添加訂單項目
    new_items = []
    for item_data in data['items']:
        product = Product.query.get(item_data['product_id'])
        if not product:
            return jsonify({"message": f"Product {item_data['product_id']} not found!"}), 404
        
        quantity = int(item_data['quantity'])
        if quantity <= 0:
            return jsonify({"message": "Quantity must be greater than 0!"}), 400
        
        unit_price = product.price
        total_price = unit_price * quantity
        
        new_items.append({
            'product': product,
            'quantity': quantity,
            'unit_price': unit_price,
            'total_price': total_price
        })
    
    # 如果存在相同的發票，添加到現有發票
    if existing_invoice:
        invoice = existing_invoice
        message = f"Order added to existing invoice! {invoice.invoice_number}！"
    else:
        # 創建新發票
        invoice_number = generate_invoice_number()
        invoice = Invoice(
            invoice_number=invoice_number,
            customer_id=data['customer_id'],
            delivery_date=delivery_date,
            status='Pending'
        )
        db.session.add(invoice)
        db.session.flush()  # 獲取 invoice.id
        message = f"Invoice {invoice_number} created successfully!"
    
    # 添加所有新的訂單項目
    for item_info in new_items:
        order_item = OrderItem(
            invoice_id=invoice.id,
            product_id=item_info['product'].id,
            quantity=item_info['quantity'],
            unit_price=item_info['unit_price'],
            total_price=item_info['total_price']
        )
        db.session.add(order_item)
    
    # 更新發票總金額
    invoice.calculate_total()
    db.session.commit()
    
    return jsonify({
        "message": message,
        "invoice": invoice.to_dict()
    }), 201

@invoices_bp.route("/<int:invoice_id>", methods=["PUT"])
def update_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    data = request.json
    
    if 'status' in data:
        invoice.status = data['status']
    
    if 'delivery_date' in data:
        try:
            invoice.delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({"message": "Invalid date format!"}), 400
    
    # 更新訂單項目數量
    if 'items' in data:
        for item_data in data['items']:
            order_item = OrderItem.query.get(item_data['id'])
            if order_item and order_item.invoice_id == invoice_id:
                quantity = int(item_data.get('quantity', order_item.quantity))
                if quantity <= 0:
                    return jsonify({"message": "Quantity must be greater than 0!"}), 400
                order_item.quantity = quantity
                order_item.total_price = order_item.unit_price * quantity
    
    invoice.calculate_total()
    db.session.commit()
    
    return jsonify({"message": "Invoice updated successfully!", "invoice": invoice.to_dict()})

@invoices_bp.route("/<int:invoice_id>", methods=["DELETE"])
def delete_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    db.session.delete(invoice)
    db.session.commit()
    
    return jsonify({"message": "Invoice deleted successfully!"})

@invoices_bp.route("/cutting-list/<date>/pdf", methods=["GET"])
def generate_cutting_list_pdf(date):
    """生成指定日期的 Cutting List PDF"""
    try:
        delivery_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"message": "Invalid date format!"}), 400
    
    # 獲取該日期的所有發票
    invoices = Invoice.query.filter_by(delivery_date=delivery_date).all()
    
    if not invoices:
        return jsonify({"message": "No orders for this date!"}), 404
    
    # 按客戶分組
    customer_groups = {}
    for invoice in invoices:
        customer_name = invoice.customer.name
        if customer_name not in customer_groups:
            customer_groups[customer_name] = []
        customer_groups[customer_name].append(invoice)
    
    # 創建 PDF
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    # 標題 - 日期
    title_style = styles['Title']
    title = Paragraph(f"<b>{date}</b>", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # 按客戶名稱排序
    sorted_customers = sorted(customer_groups.keys())
    
    for customer_name in sorted_customers:
        customer_invoices = customer_groups[customer_name]
        
        # 準備該客戶的表格數據
        table_data = []
        
        for idx, invoice in enumerate(customer_invoices):
            if idx == 0:
                # ROW 1: 客戶名稱 | 第一個產品 | 數量 | 空格
                if invoice.order_items:
                    first_item = invoice.order_items[0]
                    table_data.append([
                        customer_name,
                        first_item.product.name,
                        str(first_item.quantity),
                        ''
                    ])
                    
                    # 如果第一張發票有多個產品，添加到 ROW1 之後
                    for item in invoice.order_items[1:]:
                        table_data.append([
                            '',
                            item.product.name,
                            str(item.quantity),
                            ''
                        ])
                
                # ROW 2: 發票號碼 | 第二個產品（如果第二張發票存在）| 空格 | 空格
                second_product = ''
                if len(customer_invoices) > 1 and customer_invoices[1].order_items:
                    second_product = customer_invoices[1].order_items[0].product.name
                
                table_data.append([
                    invoice.invoice_number,
                    second_product,
                    '',
                    ''
                ])
            elif idx == 1:
                # 第二張發票的剩餘產品
                for item_idx, item in enumerate(invoice.order_items):
                    if item_idx == 0:
                        continue  # 第一個已經在 ROW2 顯示
                    table_data.append([
                        '',
                        item.product.name,
                        str(item.quantity),
                        ''
                    ])
                
                # 添加發票號碼
                table_data.append([
                    invoice.invoice_number,
                    '',
                    '',
                    ''
                ])
            else:
                # 第三張及以後的發票
                for item in invoice.order_items:
                    table_data.append([
                        '',
                        item.product.name,
                        str(item.quantity),
                        ''
                    ])
                
                table_data.append([
                    invoice.invoice_number,
                    '',
                    '',
                    ''
                ])
        
        # ROW 3: 空行（方便閱讀）
        table_data.append(['', '', '', ''])
        
        # 創建表格
        customer_table = Table(table_data, colWidths=[2*inch, 2.5*inch, 1*inch, 1*inch])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),  # 客戶名稱加粗
            ('FONTSIZE', (0, 0), (0, 0), 12),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),  # 除了最後一行空行
            ('LINEBELOW', (0, -2), (-1, -2), 1, colors.black),  # 表格底部線
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(customer_table)
        elements.append(Spacer(1, 0.2*inch))
    
    # 生成 PDF
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'cutting_list_{date}.pdf',
        mimetype='application/pdf'
    )

@invoices_bp.route("/<int:invoice_id>/pdf", methods=["GET"])
def generate_invoice_pdf(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # 標題
    title = Paragraph("<b>INVOICE</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # 發票信息
    invoice_info = [
        ['Invoice Number:', invoice.invoice_number],
        ['Invoice Date:', invoice.created_date.strftime('%Y-%m-%d %H:%M:%S')],
        ['Delivery Date:', invoice.delivery_date.strftime('%Y-%m-%d')],
        ['Status:', invoice.status]
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
        ['Customer ID:', str(invoice.customer_id)],
        ['Customer Name:', invoice.customer.name],
        ['Email:', invoice.customer.email]
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
    
    data = [['Product ID', 'Product Name', 'Unit Price', 'Quantity', 'Total']]
    
    for item in invoice.order_items:
        data.append([
            item.product_id,
            item.product.name,
            f'${item.unit_price:.2f}',
            str(item.quantity),
            f'${item.total_price:.2f}'
        ])
    
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
    total_data = [['Total Amount:', f'${invoice.total_amount:.2f}']]
    total_table = Table(total_data, colWidths=[4.5*inch, 2*inch])
    total_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.black),
    ]))
    elements.append(total_table)
    
    doc.build(elements)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'invoice_{invoice.invoice_number}.pdf',
        mimetype='application/pdf'
    )
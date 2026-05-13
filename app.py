from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime
import json
import re
import os
import resend
import threading
import time

app = Flask(__name__)
app.config['DATABASE'] = 'brain.db'
BASE_URL = os.environ.get('BASE_URL', 'https://kovi-lehoai.onrender.com').rstrip('/')

# Cấu hình Resend
try:
    with open('static/resend_config.txt', 'r') as f:
        resend.api_key = f.read().strip()
except Exception as e:
    print(f"Lỗi đọc Resend API Key: {e}")

def init_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()
    # Tạo các bảng nếu chưa có (rút gọn từ setup_db.py)
    cursor.execute('''CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT UNIQUE, zalo TEXT, email TEXT, address TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, price REAL NOT NULL, quantity_available INTEGER DEFAULT 0, description TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, product_id INTEGER, quantity INTEGER, total_amount REAL, status TEXT DEFAULT 'pending', order_date DATETIME DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (customer_id) REFERENCES customers (id), FOREIGN KEY (product_id) REFERENCES products (id))''')
    
    # Thêm dữ liệu mẫu nếu bảng products trống
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO products (name, price, quantity_available, description) VALUES (?, ?, ?, ?)', ('Đông Trùng Hạ Thảo Khô', 600000, 100, 'Tặng kèm táo đỏ'))
        cursor.execute('INSERT INTO products (name, price, quantity_available, description) VALUES (?, ?, ?, ?)', ('Đông Trùng Hạ Thảo Tươi', 200000, 50, 'Giữ nguyên dược chất'))
    
    conn.commit()
    conn.close()

init_db()

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response

@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return jsonify({'success': True})


def get_db():
    """Lấy kết nối database"""
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def send_notification_email(order_data):
    """Gửi email thông báo đơn hàng mới qua Resend (Dành cho Admin)"""
    try:
        params = {
            "from": "KOVI Landing Page <onboarding@resend.dev>",
            "to": ["hoailt777@gmail.com"],
            "subject": f"ORDER NOTIFICATION #{order_data['id']} - {order_data['customer_name']}",
            "html": f"""
                <h2>Bạn có đơn hàng mới từ Landing Page!</h2>
                <p><strong>Khách hàng:</strong> {order_data['customer_name']}</p>
                <p><strong>Số điện thoại:</strong> {order_data['phone']}</p>
                <p><strong>Email:</strong> {order_data.get('email', 'N/A')}</p>
                <p><strong>Sản phẩm:</strong> {order_data['product_name']}</p>
                <p><strong>Số lượng:</strong> {order_data['quantity']}</p>
                <p><strong>Tổng tiền:</strong> {order_data['total_amount']:,.0f} đ</p>
                <p><strong>Địa chỉ:</strong> {order_data['address']}</p>
                <hr>
                <p><a href="{BASE_URL}/admin">Truy cập trang Admin để quản lý</a></p>
            """.format(BASE_URL=BASE_URL)
        }
        print(f"Đang gửi email thông báo cho đơn hàng #{order_data['id']}...")
        r = resend.Emails.send(params)
        print(f"Kết quả gửi email Resend: {r}")
    except Exception as e:
        print(f"ERROR SENDING ADMIN NOTIFICATION: {str(e)}")

# ========== EMAIL CONFIG & TEMPLATES ==========

EMAIL_TEMPLATES = {
    1: {
        "subject": "[KOVI] Chào mừng bạn đồng hành cùng hành trình sức khỏe tinh tế",
        "html": """
            <p>Chào {name},</p>
            <p>Rất vui vì bạn đã chọn KOVI là điểm dừng chân trong hành trình tìm kiếm sự cân bằng và phục hồi thể trạng.</p>
            <p>Tại KOVI, chúng tôi không chỉ cung cấp những sản phẩm từ Đông Trùng Hạ Thảo, mà còn mong muốn trở thành người đồng hành điềm đạm, thấu hiểu trên con đường chăm sóc sức khỏe của bạn. Chúng tôi tin rằng, sức khỏe là một khoản đầu tư vô giá và cần được "bảo dưỡng" mỗi ngày một cách khoa học.</p>
            <p>Trong những ngày tới, tôi sẽ chia sẻ thêm với bạn về triết lý chăm sóc sức khỏe từ gốc mà KOVI đang theo đuổi. Hãy dành một chút thời gian để cùng lắng nghe cơ thể mình nhé.</p>
            <p>Hẹn gặp lại bạn trong email tiếp theo,</p>
            <p><strong>Đội ngũ KOVI</strong><br><em>Chăm sóc từ gốc</em></p>
        """
    },
    2: {
        "subject": "Triết lý 'Bảo dưỡng' cơ thể: Tại sao cần chăm sóc từ gốc?",
        "html": """
            <p>Chào {name},</p>
            <p>Trong cuộc sống bận rộn, chúng ta thường chỉ chú ý đến sức khỏe khi cơ thể bắt đầu lên tiếng bằng những cơn mệt mỏi hay đau nhức. Nhưng bạn có bao giờ tự hỏi, tại sao chúng ta lại đợi đến lúc "hỏng" mới sửa?</p>
            <p>Tại KOVI, chúng tôi tin vào khái niệm <strong>"Bảo dưỡng thể trạng"</strong>.</p>
            <p>Cũng giống như một cỗ máy quý giá, cơ thể cần được chăm sóc từ những tế bào nhỏ nhất, ngay từ khi mọi thứ vẫn đang ổn định. Thay vì tìm kiếm những phương pháp tức thời, việc bồi bổ một cách điềm đạm và bền bỉ mới là chìa khóa để phục hồi năng lượng thực sự.</p>
            <p>Một chút thay đổi nhỏ trong thói quen hằng ngày, như việc dành 5 phút tĩnh lặng thưởng một tách trà dược liệu, chính là cách bạn đang "tưới nước" cho cái gốc sức khỏe của mình.</p>
            <p>Ngày mai, tôi sẽ chia sẻ với bạn giải pháp cụ thể mà KOVI đã dành tâm huyết nghiên cứu để giúp quá trình "bảo dưỡng" này trở nên tinh tế và hiệu quả nhất.</p>
            <p>Chúc bạn một ngày bình yên,</p>
            <p><strong>Đội ngũ KOVI</strong></p>
        """
    },
    3: {
        "subject": "Giải pháp tinh tế cho một sức khỏe bền vững",
        "html": """
            <p>Chào {name},</p>
            <p>Sau những chia sẻ về triết lý chăm sóc sức khỏe, hôm nay tôi muốn giới thiệu tới bạn những giải pháp tâm huyết nhất tại KOVI – nơi dược tính thiên nhiên gặp gỡ sự thấu cảm sâu sắc.</p>
            <p>Nếu bạn đang tìm kiếm một cách để phục hồi thể trạng và tăng cường sức đề kháng một cách bền vững, đây là những lựa chọn được khách hàng của chúng tôi tin dùng nhất:</p>
            <ol>
                <li><strong>Combo Đông Trùng Hạ Thảo Khô (Tặng kèm Táo Đỏ):</strong> Một sự kết hợp tinh tế để pha trà hoặc hầm thực phẩm, giúp cải thiện giấc ngủ và bảo dưỡng hệ hô hấp, tim mạch.</li>
                <li><strong>Cao Tinh Chất Mật Ong:</strong> Giải pháp tiện lợi cho mỗi buổi sáng, giúp nạp năng lượng và chăm sóc hệ tiêu hóa, gan thận từ gốc.</li>
            </ol>
            <p>Chúng tôi không nói về những kết quả thần kỳ sau một đêm, nhưng chúng tôi tin vào sự thay đổi tích cực của cơ thể khi được nuôi dưỡng đúng cách bằng nguồn nguyên liệu đạt chuẩn HACCP và OCOP 4 sao.</p>
            <p>Đây chính là khoản đầu tư thông minh cho chính bạn và những người thân yêu.</p>
            <p>👉 <strong><a href="{BASE_URL}/">Xem chi tiết sản phẩm và đặt hàng tại đây</a></strong></p>
            <p>Nếu bạn cần thêm bất kỳ sự tư vấn chuyên sâu nào, đừng ngần ngại phản hồi email này. Tôi luôn ở đây để lắng nghe.</p>
            <p>Trân trọng,</p>
            <p><strong>Đội ngũ KOVI</strong></p>
        """
    }
}

def send_sequence_email(email, name, step):
    """Gửi email theo từng bước trong chuỗi sequence"""
    log_msg = ""
    try:
        template = EMAIL_TEMPLATES.get(step)
        if not template:
            return

        # Xử lý giới hạn Sandbox của Resend
        recipient = email
        if "+test" in email.lower():
            recipient = "hoailt777@gmail.com"

        params = {
            "from": "KOVI <onboarding@resend.dev>",
            "to": [recipient],
            "subject": template["subject"],
            "html": template["html"].format(name=name, BASE_URL=BASE_URL)
        }
        log_msg = f"--- Sending Email {step} to {email} ---\n"
        resend.Emails.send(params)
        log_msg += f"SUCCESS: Email {step} sent.\n"
    except Exception as e:
        log_msg += f"ERROR SENDING EMAIL SEQUENCE {step}: {str(e)}\n"
    
    print(log_msg, end="")
    try:
        with open("sequence_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {log_msg}")
    except:
        pass

def send_order_confirmation_email(customer_email, customer_name, product_name, total_amount):
    """Gửi email xác nhận đơn hàng khi Admin tạo đơn mới"""
    if not customer_email:
        return
        
    # Xử lý giới hạn Sandbox
    recipient = customer_email
    if "+test" in customer_email.lower():
        recipient = "hoailt777@gmail.com"
        
    try:
        params = {
            "from": "KOVI <onboarding@resend.dev>",
            "to": [recipient],
            "subject": "[KOVI] Xác nhận đơn hàng của bạn - Cảm ơn bạn đã tin chọn sự tử tế",
            "html": f"""
                <p>Chào {customer_name},</p>
                <p>KOVI đã nhận được đơn hàng của bạn. Cảm ơn bạn đã trao cho chúng tôi cơ hội được đồng hành trong hành trình "bảo dưỡng" sức khỏe của bạn và gia đình.</p>
                <p>Dưới đây là thông tin chi tiết về sự lựa chọn của bạn:</p>
                <ul>
                    <li><strong>Sản phẩm:</strong> {product_name}</li>
                    <li><strong>Tổng giá trị:</strong> {total_amount:,.0f} đ</li>
                </ul>
                <p><strong>Hướng dẫn nhận hàng:</strong><br>
                Đơn hàng của bạn đang được chúng tôi chuẩn bị một cách cẩn trọng nhất. Chuyên viên giao hàng sẽ liên hệ với bạn trong vòng 2-3 ngày tới. Khi nhận hàng, bạn vui lòng kiểm tra kỹ sản phẩm trước khi thanh toán.</p>
                <p>Chúng tôi tin rằng, mỗi sản phẩm từ KOVI không chỉ là một món quà thảo dược, mà còn là lời hứa về sự bền bỉ và thấu cảm. Hy vọng bạn sẽ tìm thấy sự thư thái khi sử dụng sản phẩm này.</p>
                <p>Nếu có bất kỳ thắc mắc nào, hãy phản hồi lại email này. Chúng tôi luôn sẵn lòng lắng nghe.</p>
                <p>Trân trọng,<br><strong>Đội ngũ KOVI</strong><br><em>Chăm sóc từ gốc</em></p>
            """
        }
        log_msg = f"--- Sending Order Confirmation to {customer_email} ---\n"
        resend.Emails.send(params)
        log_msg += "SUCCESS: Order Confirmation sent.\n"
    except Exception as e:
        log_msg = f"ERROR SENDING ORDER CONFIRMATION to {customer_email}: {str(e)}\n"
    
    print(log_msg, end="")
    try:
        with open("order_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {log_msg}")
    except:
        pass

def trigger_email_sequence(email, name):
    """Kích hoạt chuỗi email tự động cho khách hàng mới"""
    if not email:
        return

    # Bước 1: Gửi ngay lập tức (Email chào mừng)
    send_sequence_email(email, name, 1)

    log_msg = ""
    # Chế độ Test: Nếu email chứa '+test', gửi tất cả ngay
    if "+test" in email.lower():
        log_msg = f"TEST MODE: Sending Email 2 and 3 immediately for {email}\n"
        send_sequence_email(email, name, 2)
        send_sequence_email(email, name, 3)
    else:
        # Chế độ Production: Hẹn giờ
        # Email 2: Sau 2 ngày (172800 giây)
        threading.Timer(172800, send_sequence_email, args=[email, name, 2]).start()
        # Email 3: Sau 3 ngày (259200 giây)
        threading.Timer(259200, send_sequence_email, args=[email, name, 3]).start()
        log_msg = f"SCHEDULED: Email 2 (2 days) and Email 3 (3 days) for {email}\n"
    
    print(log_msg, end="")
    try:
        with open("sequence_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {log_msg}")
    except:
        pass

# ========== ROUTES =========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/pay')
def pay():
    order = {
        'id': 0,
        'customer_name': 'Khách Test',
        'phone': '0900000000',
        'product_name': 'Thanh toán thử Sepay',
        'quantity': 1,
        'total_amount': 2000,
        'address': 'Hà Nội',
        'status': 'pending'
    }
    qr_text = 'ORDERTEST'
    return render_template('checkout.html', error=None, order=order, qr_text=qr_text)

@app.route('/checkout', methods=['POST'])
def checkout():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    product_id = request.form.get('product_id')
    address = request.form.get('address', '').strip()
    quantity = int(request.form.get('quantity', 1)) if request.form.get('quantity') else 1

    if not name or not phone or not product_id:
        return render_template('checkout.html', error='Vui lòng điền đầy đủ thông tin và chọn sản phẩm.', order=None)

    is_consultation = (product_id == 'tu-van')
    product = None
    total_amount = 0

    if not is_consultation:
        try:
            product_id = int(product_id)
        except ValueError:
            return render_template('checkout.html', error='Sản phẩm không hợp lệ.', order=None)

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE id=?', (product_id,))
        product = cursor.fetchone()
        if not product:
            conn.close()
            return render_template('checkout.html', error='Sản phẩm không tồn tại.', order=None)

        if product['quantity_available'] < quantity:
            conn.close()
            return render_template('checkout.html', error=f'Hiện chỉ còn {product["quantity_available"]} sản phẩm.', order=None)
        total_amount = product['price'] * quantity
        conn.close()

    # Xử lý thông tin khách hàng (Cả đặt hàng và tư vấn đều lưu khách hàng)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM customers WHERE phone=?', (phone,))
    customer = cursor.fetchone()
    if customer:
        customer_id = customer['id']
        cursor.execute(
            'UPDATE customers SET name=?, address=?, email=? WHERE id=?',
            (name, address, email, customer_id)
        )
    else:
        cursor.execute(
            'INSERT INTO customers (name, phone, address, email) VALUES (?, ?, ?, ?)',
            (name, phone, address, email)
        )
        customer_id = cursor.lastrowid

    order_id = None
    if not is_consultation:
        # Tạo đơn hàng nếu không phải tư vấn
        cursor.execute(
            'INSERT INTO orders (customer_id, product_id, quantity, total_amount, status) VALUES (?, ?, ?, ?, ?)',
            (customer_id, product_id, quantity, total_amount, 'pending')
        )
        order_id = cursor.lastrowid

        cursor.execute(
            'UPDATE products SET quantity_available = quantity_available - ? WHERE id=?',
            (quantity, product_id)
        )

    conn.commit()
    conn.close()

    # Kích hoạt chuỗi email tự động nếu có email
    if email:
        trigger_email_sequence(email, name)

    if is_consultation:
        # Nếu là tư vấn, trả về thông báo thành công
        order = {
            'customer_name': name,
            'is_consultation': True
        }
        return render_template('checkout.html', error=None, order=order, qr_text=None)

    order = {
        'id': order_id,
        'customer_name': name,
        'phone': phone,
        'email': email,
        'product_name': product['name'],
        'quantity': quantity,
        'total_amount': total_amount,
        'address': address,
        'status': 'pending'
    }

    qr_text = f"ORDER{order_id}"
    
    # Gửi email thông báo cho Admin (đơn hàng mới)
    send_notification_email(order)
    
    return render_template('checkout.html', error=None, order=order, qr_text=qr_text)

# ========== PRODUCTS API ==========

@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products ORDER BY id DESC')
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(products)

@app.route('/api/products', methods=['POST'])
def add_product():
    if not request.is_json:
        return jsonify({'error': 'Request body must be JSON'}), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    name = data.get('name')
    price = data.get('price')
    quantity_available = data.get('quantity_available')
    description = data.get('description', '')

    if not name or price is None or quantity_available is None:
        return jsonify({'error': 'Thiếu dữ liệu sản phẩm'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO products (name, price, description, quantity_available) VALUES (?, ?, ?, ?)',
        (name, price, description, quantity_available)
    )
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    return jsonify({'id': product_id, 'success': True}), 201

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    if not request.is_json:
        return jsonify({'error': 'Request body must be JSON'}), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON payload'}), 400

    name = data.get('name')
    price = data.get('price')
    quantity_available = data.get('quantity_available')
    description = data.get('description', '')

    if not name or price is None or quantity_available is None:
        return jsonify({'error': 'Thiếu dữ liệu sản phẩm'}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE products SET name=?, price=?, description=?, quantity_available=? WHERE id=?',
        (name, price, description, quantity_available, product_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id=?', (product_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ========== CUSTOMERS API ==========

@app.route('/api/customers', methods=['GET'])
def get_customers():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM customers ORDER BY id DESC')
    customers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(customers)

@app.route('/api/customers', methods=['POST'])
def add_customer():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            'INSERT INTO customers (name, phone, zalo, email, address) VALUES (?, ?, ?, ?)',
            (data['name'], data.get('phone'), data.get('zalo'), data.get('email'), data.get('address'))
        )
        conn.commit()
        customer_id = cursor.lastrowid
        conn.close()
        return jsonify({'id': customer_id, 'success': True}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Số điện thoại đã tồn tại'}), 400

@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        'UPDATE customers SET name=?, phone=?, zalo=?, email=?, address=? WHERE id=?',
        (data['name'], data.get('phone'), data.get('zalo'), data.get('email'), data.get('address'), customer_id)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM customers WHERE id=?', (customer_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# ========== ORDERS API ==========

@app.route('/api/orders', methods=['GET'])
def get_orders():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT o.*, c.name as customer_name, p.name as product_name, p.price
        FROM orders o
        JOIN customers c ON o.customer_id = c.id
        JOIN products p ON o.product_id = p.id
        ORDER BY o.id DESC
    ''')
    orders = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(orders)

@app.route('/api/orders/<int:order_id>/status', methods=['GET', 'PUT'])
def handle_order_status(order_id):
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT status FROM orders WHERE id=?', (order_id,))
        order = cursor.fetchone()
        conn.close()
        if order:
            return jsonify({'status': order['status']})
        return jsonify({'error': 'Order not found'}), 404
    
    elif request.method == 'PUT':
        data = request.json
        status = data.get('status')
        if not status:
            conn.close()
            return jsonify({'success': False, 'message': 'Missing status'}), 400
        
        cursor.execute('UPDATE orders SET status=? WHERE id=?', (status, order_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/orders', methods=['POST'])
def add_order():
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Lấy thông tin sản phẩm để kiểm tra số lượng
        cursor.execute('SELECT quantity_available FROM products WHERE id=?', (data['product_id'],))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'error': 'Sản phẩm không tồn tại'}), 400
        
        if product['quantity_available'] < data['quantity']:
            return jsonify({'error': f'Không đủ hàng. Còn lại: {product["quantity_available"]}'}), 400
        
        # Thêm đơn hàng
        cursor.execute(
            'INSERT INTO orders (customer_id, product_id, quantity, total_amount, status) VALUES (?, ?, ?, ?, ?)',
            (data['customer_id'], data['product_id'], data['quantity'], data['total_amount'], 'pending')
        )
        order_id = cursor.lastrowid
        
        # Trừ số lượng sản phẩm
        new_quantity = product['quantity_available'] - data['quantity']
        cursor.execute(
            'UPDATE products SET quantity_available=? WHERE id=?',
            (new_quantity, data['product_id'])
        )
        
        conn.commit()
        
        # Gửi email xác nhận đơn hàng tự động cho khách hàng
        try:
            cursor.execute('SELECT name, email FROM customers WHERE id=?', (data['customer_id'],))
            cust = cursor.fetchone()
            cursor.execute('SELECT name FROM products WHERE id=?', (data['product_id'],))
            prod = cursor.fetchone()
            
            if cust and prod and cust['email']:
                send_order_confirmation_email(cust['email'], cust['name'], prod['name'], data['total_amount'])
        except Exception as email_err:
            print(f"Lỗi khi chuẩn bị gửi email xác nhận: {email_err}")

        conn.close()
        return jsonify({'id': order_id, 'success': True}), 201
    
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@app.route('/api/orders/<int:order_id>', methods=['PUT'])
def update_order(order_id):
    data = request.json
    conn = get_db()
    cursor = conn.cursor()
    
    # Lấy order cũ để tính toán lại quantity
    cursor.execute('SELECT product_id, quantity FROM orders WHERE id=?', (order_id,))
    old_order = cursor.fetchone()
    
    if not old_order:
        conn.close()
        return jsonify({'error': 'Đơn hàng không tồn tại'}), 400
    
    old_quantity = old_order['quantity']
    new_quantity = data.get('quantity', old_quantity)
    quantity_diff = old_quantity - new_quantity
    
    try:
        # Cập nhật đơn hàng
        cursor.execute(
            'UPDATE orders SET customer_id=?, product_id=?, quantity=?, total_amount=?, status=? WHERE id=?',
            (data['customer_id'], data['product_id'], new_quantity, data['total_amount'], data['status'], order_id)
        )
        
        # Cập nhật số lượng sản phẩm
        cursor.execute(
            'UPDATE products SET quantity_available = quantity_available + ? WHERE id=?',
            (quantity_diff, old_order['product_id'])
        )
        
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 400

@app.route('/api/orders/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    conn = get_db()
    cursor = conn.cursor()
    
    # Lấy thông tin order để hoàn lại số lượng sản phẩm
    cursor.execute('SELECT product_id, quantity FROM orders WHERE id=?', (order_id,))
    order = cursor.fetchone()
    
    if order:
        cursor.execute(
            'UPDATE products SET quantity_available = quantity_available + ? WHERE id=?',
            (order['quantity'], order['product_id'])
        )
    
    cursor.execute('DELETE FROM orders WHERE id=?', (order_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/webhook', methods=['POST'])
def sepay_webhook():
    data = request.json
    print("--- Webhook Received ---")
    
    if not data:
        return jsonify({'success': False, 'message': 'No data'}), 400
    
    content = data.get('content', '')
    # Tìm mã đơn hàng ORDERxxx
    match = re.search(r'ORDER(\d+)', content, re.IGNORECASE)
    
    if match:
        order_id = match.group(1)
        print(f"Found Order ID: {order_id}")
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Kiểm tra đơn hàng tồn tại
        cursor.execute('SELECT id FROM orders WHERE id=?', (order_id,))
        order = cursor.fetchone()
        
        if order:
            cursor.execute('UPDATE orders SET status=? WHERE id=?', ('success', order_id))
            conn.commit()
            conn.close()
            print(f"Order {order_id} updated to success")
            return jsonify({'success': True, 'message': f'Order {order_id} updated to success'})
        else:
            conn.close()
            print(f"Order {order_id} not found")
            return jsonify({'success': False, 'message': f'Order {order_id} not found'}), 404
            
    return jsonify({'success': False, 'message': 'Order ID not found in content'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

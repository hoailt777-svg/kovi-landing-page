from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
from datetime import datetime
import json
import re

app = Flask(__name__)
app.config['DATABASE'] = 'brain.db'

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
    product_id = request.form.get('product_id')
    address = request.form.get('address', '').strip()
    quantity = int(request.form.get('quantity', 1)) if request.form.get('quantity') else 1

    if not name or not phone or not product_id:
        return render_template('checkout.html', error='Vui lòng điền đầy đủ thông tin và chọn sản phẩm.', order=None)

    if product_id == 'tu-van':
        return render_template('checkout.html', error='Vui lòng chọn sản phẩm cụ thể để tiếp tục thanh toán.', order=None)

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

    cursor.execute('SELECT id FROM customers WHERE phone=?', (phone,))
    customer = cursor.fetchone()
    if customer:
        customer_id = customer['id']
        cursor.execute(
            'UPDATE customers SET name=?, address=? WHERE id=?',
            (name, address, customer_id)
        )
    else:
        cursor.execute(
            'INSERT INTO customers (name, phone, address) VALUES (?, ?, ?)',
            (name, phone, address)
        )
        customer_id = cursor.lastrowid

    total_amount = product['price'] * quantity
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

    order = {
        'id': order_id,
        'customer_name': name,
        'phone': phone,
        'product_name': product['name'],
        'quantity': quantity,
        'total_amount': total_amount,
        'address': address,
        'status': 'pending'
    }

    qr_text = f"ORDER{order_id}"
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
            'INSERT INTO customers (name, phone, zalo, email, address) VALUES (?, ?, ?, ?, ?)',
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
        
        # Trừ số lượng sản phẩm
        new_quantity = product['quantity_available'] - data['quantity']
        cursor.execute(
            'UPDATE products SET quantity_available=? WHERE id=?',
            (new_quantity, data['product_id'])
        )
        
        conn.commit()
        order_id = cursor.lastrowid
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

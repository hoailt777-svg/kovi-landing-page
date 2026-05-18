#!/usr/bin/env python3
"""MCP HTTP server (simple) for goClaw integration.

Transport: HTTP POST JSON to /mcp
Auth: Authorization: Bearer <TOKEN>

Starts Flask server on 127.0.0.1:3001 and exposes functions:
- get_order_summary
- update_order_status
- get_customer_info

Also contains a test runner that inserts a sample customer+order and
invokes the functions via curl, printing results.
"""
import os
import sqlite3
import threading
import time
import json
from flask import Flask, request, jsonify

APP_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.dirname(APP_DIR)
DB_PATH = os.path.join(ROOT_DIR, 'brain.db')

MCP_TOKEN = os.environ.get('MCP_TOKEN', 'secret-token')

app = Flask(__name__)


def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_order_summary_impl(date_from=None, status=None):
    conn = get_db_conn()
    cursor = conn.cursor()
    q = '''SELECT o.id, c.name as customer_name, p.name as product_name, o.total_amount, o.status, o.order_date
           FROM orders o
           JOIN customers c ON o.customer_id = c.id
           JOIN products p ON o.product_id = p.id
           WHERE 1=1'''
    params = []
    if date_from:
        q += ' AND date(o.order_date) >= date(?)'
        params.append(date_from)
    if status:
        q += ' AND o.status = ?'
        params.append(status)
    q += ' ORDER BY o.id DESC'
    cursor.execute(q, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {'new_orders_count': len(rows), 'orders': rows}


def update_order_status_impl(order_id, status):
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM orders WHERE id=?', (order_id,))
    if not cursor.fetchone():
        conn.close()
        return {'success': False, 'message': 'Order not found'}
    cursor.execute('UPDATE orders SET status=? WHERE id=?', (status, order_id))
    conn.commit()
    conn.close()
    return {'success': True, 'message': f'Order {order_id} updated to {status}'}


def get_customer_info_impl(phone_or_email):
    conn = get_db_conn()
    cursor = conn.cursor()
    if '@' in phone_or_email:
        cursor.execute('SELECT * FROM customers WHERE email=?', (phone_or_email,))
    else:
        cursor.execute('SELECT * FROM customers WHERE phone=?', (phone_or_email,))
    cust = cursor.fetchone()
    if not cust:
        conn.close()
        return {'customer': None, 'orders': []}
    customer = dict(cust)
    cursor.execute('''SELECT o.id, p.name as product_name, o.quantity, o.total_amount, o.status, o.order_date
                      FROM orders o
                      JOIN products p ON o.product_id = p.id
                      WHERE o.customer_id = ? ORDER BY o.id DESC''', (customer['id'],))
    orders = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return {'customer': customer, 'orders': orders}


def check_auth(request):
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1].strip()
        return token == MCP_TOKEN
    return False


@app.route('/mcp', methods=['POST'])
def mcp_call():
    if not check_auth(request):
        return jsonify({'error': 'unauthorized'}), 401
    body = request.get_json(silent=True) or {}
    name = body.get('name')
    params = body.get('params', {})
    try:
        if name == 'get_order_summary':
            return jsonify(get_order_summary_impl(params.get('date_from'), params.get('status')))
        elif name == 'update_order_status':
            return jsonify(update_order_status_impl(int(params.get('order_id')), params.get('status')))
        elif name == 'get_customer_info':
            return jsonify(get_customer_info_impl(params.get('phone_or_email') or params.get('phone') or params.get('email')))
        else:
            return jsonify({'error': 'unknown function'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def run_server():
    # Flask built-in server bound to localhost only
    app.run(host='127.0.0.1', port=3001, debug=False, use_reloader=False)


def run_tests():
    import urllib.request
    import urllib.error
    print('Running tests: preparing DB entries...')
    # create a sample customer and order to test update and get_customer_info
    conn = get_db_conn()
    cur = conn.cursor()
    # get an existing product id
    cur.execute('SELECT id, price FROM products LIMIT 1')
    prod = cur.fetchone()
    if not prod:
        print('No product found in DB; tests cannot proceed.')
        return 1
    product_id = prod['id']
    # insert customer
    cur.execute("INSERT INTO customers (name, phone, zalo, email, address) VALUES (?,?,?,?,?)",
                ('MCP Test', '0999000000', '', 'mcp@test.local', 'Test'))
    customer_id = cur.lastrowid
    # insert order
    cur.execute('INSERT INTO orders (customer_id, product_id, quantity, total_amount, status) VALUES (?,?,?,?,?)',
                (customer_id, product_id, 1, prod['price'], 'pending'))
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    print(f'Inserted customer_id={customer_id} order_id={order_id}')

    url = 'http://127.0.0.1:3001/mcp'
    headers = {'Content-Type': 'application/json', 'Authorization': f'Bearer {MCP_TOKEN}'}

    def post_json(payload):
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return resp.read().decode('utf-8')
        except urllib.error.HTTPError as e:
            return e.read().decode('utf-8')

    out1 = post_json({'name': 'get_order_summary', 'params': {'date_from': '2000-01-01'}})
    print('\n[get_order_summary] ->', out1)

    out2 = post_json({'name': 'update_order_status', 'params': {'order_id': order_id, 'status': 'success'}})
    print('\n[update_order_status] ->', out2)

    out3 = post_json({'name': 'get_customer_info', 'params': {'phone_or_email': '0999000000'}})
    print('\n[get_customer_info] ->', out3)

    # Basic verification
    ok = True
    try:
        r1 = json.loads(out1)
        r2 = json.loads(out2)
        r3 = json.loads(out3)
        if 'new_orders_count' not in r1:
            ok = False
        if not r2.get('success'):
            ok = False
        if not r3.get('customer'):
            ok = False
    except Exception as e:
        print('Error parsing results:', e)
        ok = False

    print('\nTEST RESULT:', 'PASS' if ok else 'FAIL')
    return 0 if ok else 2


if __name__ == '__main__':
    # Start server in background thread
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    # wait for server
    time.sleep(1.0)
    rc = run_tests()
    # Sleep briefly to allow prints to flush
    time.sleep(0.5)
    if rc == 0:
        print('\nAll tests passed.')
    else:
        print('\nSome tests failed.')
    # exit with code
    raise SystemExit(rc)

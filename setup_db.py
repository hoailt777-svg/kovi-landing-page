import sqlite3
import json
from datetime import datetime
import os

# Đường dẫn database
db_path = "brain.db"

# Kết nối hoặc tạo database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔧 Bắt đầu setup database...")

# 1. Tạo bảng PRODUCTS
print("\n📦 Tạo bảng products...")
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    description TEXT,
    quantity_available INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Insert sample products (3 sản phẩm KOVI)
products_data = [
    ("Combo Đông Trùng Khô (Tặng Táo Đỏ)", 600000, "Tăng sức đề kháng, chống lão hóa. Hỗ trợ tim mạch, gan, thận, phổi & sinh lý.", 50),
    ("Đông Trùng Hạ Thảo Tươi", 800000, "Giữ nguyên 100% hương vị và dược chất. Pha trà, ngâm rượu, ngâm mật ong, hầm gà.", 30),
    ("Cao Tinh Chất Mật Ong", 450000, "Tăng đề kháng, bổ phổi gan thận. Hỗ trợ giấc ngủ sâu. Chỉ 1 thìa nhỏ mỗi sáng.", 100),
]

cursor.execute("SELECT COUNT(*) FROM products")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO products (name, price, description, quantity_available) VALUES (?, ?, ?, ?)",
        products_data
    )
    print("✅ Đã thêm 3 sản phẩm mẫu")

# 2. Tạo bảng CUSTOMERS
print("\n👥 Tạo bảng customers...")
cursor.execute('''
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    phone TEXT,
    zalo TEXT,
    email TEXT,
    address TEXT,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_notified INTEGER DEFAULT 0,
    UNIQUE(phone)
)
''')

# Import từ waitlist.json nếu tồn tại
waitlist_path = "waitlist.json"
if os.path.exists(waitlist_path):
    print("📥 Đang import dữ liệu từ waitlist.json...")
    try:
        with open(waitlist_path, 'r', encoding='utf-8') as f:
            waitlist_data = json.load(f)
        
        for customer in waitlist_data:
            try:
                cursor.execute(
                    '''INSERT OR IGNORE INTO customers (name, phone, zalo, email, address) 
                       VALUES (?, ?, ?, ?, ?)''',
                    (
                        customer.get('name', 'Unknown'),
                        customer.get('phone'),
                        customer.get('zalo'),
                        customer.get('email'),
                        customer.get('address')
                    )
                )
            except Exception as e:
                print(f"⚠️  Lỗi import khách hàng: {e}")
        print(f"✅ Đã import {len(waitlist_data)} khách hàng từ waitlist.json")
    except Exception as e:
        print(f"⚠️  Không thể đọc waitlist.json: {e}")
else:
    print("ℹ️  waitlist.json không tồn tại - bỏ qua import")

# 3. Tạo bảng ORDERS
print("\n📋 Tạo bảng orders...")
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    total_amount REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES customers(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
)
''')

# Lưu database
conn.commit()

# Hiển thị tóm tắt
print("\n" + "="*50)
print("✅ DATABASE SETUP HOÀN TẤT!")
print("="*50)

# Đếm số bản ghi
cursor.execute("SELECT COUNT(*) FROM products")
products_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM customers")
customers_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM orders")
orders_count = cursor.fetchone()[0]

print(f"\n📊 Thống kê:")
print(f"   • Products: {products_count} sản phẩm")
print(f"   • Customers: {customers_count} khách hàng")
print(f"   • Orders: {orders_count} đơn hàng")
print(f"\n💾 Database: {db_path}")

conn.close()
print("\n✨ Done!")

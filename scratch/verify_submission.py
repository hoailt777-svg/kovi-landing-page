import requests

url = 'http://127.0.0.1:5000/checkout'
data = {
    'name': 'Test User',
    'phone': '0987654321',
    'email': 'test@example.com',
    'product_id': '1',
    'address': '123 Test St',
    'quantity': '1'
}

try:
    response = requests.post(url, data=data)
    print(f"Status Code: {response.status_code}")
    # print(response.text)
except Exception as e:
    print(f"Error: {e}")

# Check database
import sqlite3
conn = sqlite3.connect('brain.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM customers WHERE phone='0987654321'")
customer = cursor.fetchone()
print(f"Customer in DB: {customer}")
conn.close()

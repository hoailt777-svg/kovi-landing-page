import requests

def test():
    try:
        customers = requests.get("http://127.0.0.1:5000/api/customers").json()
        target = None
        for c in customers:
            if c.get('email') and '@' in c['email']:
                target = c
                break
        
        if not target:
            print("No customer with email found.")
            return

        products = requests.get("http://127.0.0.1:5000/api/products").json()
        
        data = {
            "customer_id": target['id'],
            "product_id": products[0]['id'],
            "quantity": 1,
            "total_amount": 5000,
            "status": "pending"
        }
        
        print("Sending request...")
        r = requests.post("http://127.0.0.1:5000/api/orders", json=data)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()

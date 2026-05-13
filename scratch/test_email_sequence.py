import requests
import sys

def test_sequence():
    url = "http://127.0.0.1:5000/checkout"

    # Test Case 1: Consultation with +test email
    data = {
        "name": "Khach Test Sequence",
        "phone": "0988888888",
        "email": "hoailt777+test@gmail.com",
        "product_id": "tu-van",
        "address": "Ha Noi"
    }

    print("Testing consultation with +test email...")
    try:
        response = requests.post(url, data=data)
        print(f"Status Code: {response.status_code}")
        if "Cam on ban da dang ky tu van" in response.text or "Cảm ơn bạn đã đăng ký tư vấn" in response.text:
            print("OK: Consultation success view displayed.")
        else:
            print("FAIL: Failed to display consultation success view.")
    except Exception as e:
        print(f"ERROR: {e}")

    # Test Case 2: Order with +test email
    data_order = {
        "name": "Khach Test Order",
        "phone": "0977777777",
        "email": "hoailt777+test_order@gmail.com",
        "product_id": "1", 
        "address": "Ha Noi",
        "quantity": "1"
    }

    print("\nTesting order with +test email...")
    try:
        response_order = requests.post(url, data=data_order)
        print(f"Status Code: {response_order.status_code}")
        if "Don hang cua ban da duoc luu" in response_order.text or "Đơn hàng của bạn đã được lưu" in response_order.text:
            print("OK: Order success view displayed.")
        else:
            print("FAIL: Failed to display order success view.")
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_sequence()

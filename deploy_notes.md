# Deploy Notes

## Biến môi trường cần có trên VPS

- `RESEND_API_KEY` - API key của Resend để gửi email.
- `BASE_URL` - URL production của website, ví dụ: `https://your-domain.com`.
- `ADMIN_EMAIL` - email nhận thông báo đơn hàng.
- `FLASK_ENV` - môi trường Flask, nên đặt `production`.
- `PORT` - cổng server sẽ lắng nghe (mặc định `3000`).
- `HOST` - host để server lắng nghe (mặc định `0.0.0.0`).

## Lệnh chạy server

1. Chuẩn bị môi trường Python và cài dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Tạo file `.env` và điền các biến:

```ini
RESEND_API_KEY=re_your_actual_key_here
BASE_URL=https://your-domain.com
ADMIN_EMAIL=your-email@gmail.com
FLASK_ENV=production
PORT=3000
HOST=0.0.0.0
```

3. Khởi động server trong môi trường ảo:

```bash
source venv/bin/activate
python app.py
```

4. Hoặc dùng Gunicorn (production):

```bash
gunicorn --bind 0.0.0.0:${PORT:-3000} app:app
```

## Cổng đang lắng nghe

- Mặc định: `3000`
- Nếu đặt `PORT` trong `.env`, server sẽ lắng nghe cổng đó.

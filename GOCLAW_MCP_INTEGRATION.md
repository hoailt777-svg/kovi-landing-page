# 🎯 goClaw Agent - MCP Server Integration Guide

**Date:** May 18, 2026  
**MCP Server Status:** ✅ Active & Running on VPS port 3001

---

## 📋 MCP Server Configuration

### Server Details
```
Host:         103.97.127.67 (VPS)
Port:         3001
Bind:         127.0.0.1 (internal only)
Protocol:     HTTP
Endpoint:     http://127.0.0.1:3001/mcp
Auth Type:    Bearer Token
Token:        secret-token
```

### Systemd Service
```
Service Name: mcp-server
Status:       active (running)
Workers:      2 (Gunicorn)
Restart:      automatic
Logs:         journalctl -u mcp-server -f
```

---

## 🔌 Available MCP Functions

### 1. get_order_summary
**Purpose:** Retrieve all orders with optional filtering by date and status

**Request:**
```json
{
  "name": "get_order_summary",
  "params": {
    "date_from": "2026-05-01",  // Optional: ISO date (YYYY-MM-DD)
    "status": "pending"          // Optional: "pending", "success", etc.
  }
}
```

**Response:**
```json
{
  "new_orders_count": 18,
  "orders": [
    {
      "id": 18,
      "customer_name": "MCP Test",
      "product_name": "Combo Đông Trùng Khô (Tặng Táo Đỏ)",
      "total_amount": 600000.0,
      "status": "pending",
      "order_date": "2026-05-18 15:45:42"
    },
    ...more orders...
  ]
}
```

---

### 2. update_order_status
**Purpose:** Update order status to trigger notifications/workflows

**Request:**
```json
{
  "name": "update_order_status",
  "params": {
    "order_id": 18,
    "status": "success"  // e.g., "pending", "success", "shipped", "cancelled"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Order 18 updated to success"
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Order not found"
}
```

---

### 3. get_customer_info
**Purpose:** Lookup customer by phone or email and retrieve their orders

**Request:**
```json
{
  "name": "get_customer_info",
  "params": {
    "phone_or_email": "0999000000"  // or "customer@email.com"
  }
}
```

**Response:**
```json
{
  "customer": {
    "id": 7,
    "name": "MCP Test",
    "phone": "0999000000",
    "zalo": "",
    "email": "mcp@test.local",
    "address": "Test",
    "registered_at": "2026-05-18 15:45:42"
  },
  "orders": [
    {
      "id": 18,
      "product_name": "Combo Đông Trùng Khô (Tặng Táo Đỏ)",
      "quantity": 1,
      "total_amount": 600000.0,
      "status": "success",
      "order_date": "2026-05-18 15:45:42"
    }
  ]
}
```

**Error Response:**
```json
{
  "customer": null,
  "orders": []
}
```

---

## 🔐 Authentication

All requests **must** include Bearer token in the Authorization header:

```
Authorization: Bearer secret-token
```

**Example with curl:**
```bash
curl -X POST \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"get_order_summary","params":{}}' \
  http://127.0.0.1:3001/mcp
```

---

## 🌐 Integration Options for goClaw

Since MCP server binds to **127.0.0.1:3001** (internal only), you have these options:

### Option A: SSH Tunnel (Local Development)
```bash
# From your local machine where goClaw runs:
ssh -L 3001:127.0.0.1:3001 root@103.97.127.67 -p 2018

# goClaw config:
# - Endpoint: http://localhost:3001/mcp
# - Token: secret-token
```

### Option B: Caddy Reverse Proxy (Production - HTTPS)
Edit `/etc/caddy/Caddyfile` on VPS:
```
lehoai.com/mcp {
    reverse_proxy 127.0.0.1:3001
}
```

Then reload Caddy:
```bash
systemctl reload caddy
```

goClaw config:
```
- Endpoint: https://lehoai.com/mcp
- Token: secret-token
```

### Option C: Bind to All Interfaces (Less Secure)
**Only if goClaw is on a different machine with firewall protection**

On VPS, edit systemd service:
```bash
sudo systemctl edit mcp-server
```

Change this line:
```diff
- ExecStart=/opt/my-website/venv/bin/gunicorn --bind 127.0.0.1:3001 ...
+ ExecStart=/opt/my-website/venv/bin/gunicorn --bind 0.0.0.0:3001 ...
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart mcp-server
```

goClaw config:
```
- Endpoint: http://103.97.127.67:3001/mcp
- Token: secret-token
- Firewall: Only allow goClaw server IP
```

---

## ✅ Testing Integration

### Test 1: Basic Connectivity (with token)
```bash
# On VPS
curl -X POST \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"get_order_summary","params":{}}' \
  http://127.0.0.1:3001/mcp
```

Expected: JSON response with orders list

### Test 2: Authorization Check (no token)
```bash
curl http://127.0.0.1:3001/mcp
```

Expected: `{"error":"unauthorized"}` with HTTP 401

### Test 3: Invalid Token
```bash
curl -H "Authorization: Bearer wrong-token" \
  http://127.0.0.1:3001/mcp
```

Expected: `{"error":"unauthorized"}` with HTTP 401

### Test 4: Full Function Call
```bash
curl -X POST \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"get_customer_info",
    "params":{"phone_or_email":"0999000000"}
  }' \
  http://127.0.0.1:3001/mcp
```

Expected: Customer data JSON response

---

## 📝 goClaw Configuration Example

If goClaw has a config file or environment variables for MCP:

```yaml
# goClaw config (example)
mcp:
  enabled: true
  type: http
  endpoint: http://127.0.0.1:3001/mcp  # or https://lehoai.com/mcp
  auth:
    type: bearer
    token: secret-token
  timeout: 30
  retry: 3
```

Or environment variables:
```bash
export GOCLAW_MCP_ENDPOINT="http://127.0.0.1:3001/mcp"
export GOCLAW_MCP_TOKEN="secret-token"
export GOCLAW_MCP_TIMEOUT="30"
```

---

## 🔍 Monitoring & Logs

### View Real-time Logs
```bash
ssh root@103.97.127.67 -p 2018
sudo journalctl -u mcp-server -f
```

### Check Last 50 Log Entries
```bash
sudo journalctl -u mcp-server -n 50
```

### Verify Service Status
```bash
sudo systemctl status mcp-server
```

### Check Port Listening
```bash
sudo ss -tlnp | grep 3001
# or
sudo netstat -tlnp | grep 3001
```

---

## ⚠️ Troubleshooting

### MCP Server Not Responding

1. **Check if service is running:**
   ```bash
   sudo systemctl status mcp-server
   ```

2. **Restart service:**
   ```bash
   sudo systemctl restart mcp-server
   sleep 2
   sudo systemctl status mcp-server
   ```

3. **Check logs for errors:**
   ```bash
   sudo journalctl -u mcp-server -n 100
   ```

4. **Verify port is listening:**
   ```bash
   sudo ss -tlnp | grep 3001
   ```

### Authorization Failed

1. **Verify token in request:**
   ```bash
   # Should have exact token
   curl -H "Authorization: Bearer secret-token" http://127.0.0.1:3001/mcp
   ```

2. **Check if token is set in service:**
   ```bash
   sudo systemctl cat mcp-server | grep MCP_TOKEN
   ```

3. **If token changed, update service:**
   ```bash
   sudo systemctl edit mcp-server
   # Change: Environment="MCP_TOKEN=new-token"
   sudo systemctl daemon-reload
   sudo systemctl restart mcp-server
   ```

### Database Connection Issues

1. **Check if brain.db exists:**
   ```bash
   ls -lh /opt/my-website/brain.db
   ```

2. **Verify permissions:**
   ```bash
   ls -l /opt/my-website/brain.db
   # Should be readable by root user
   ```

3. **Check for SQLite errors in logs:**
   ```bash
   sudo journalctl -u mcp-server -n 50 | grep -i "database\|sqlite\|error"
   ```

---

## 🚀 Next Steps

1. **Choose integration option** (A, B, or C above)
2. **Configure goClaw** with the MCP endpoint and token
3. **Test connectivity** using the curl examples
4. **Monitor logs** during first agent calls
5. **Setup alerts** for service crashes (optional)

---

## 📞 Support

For issues or questions:
1. Check logs: `sudo journalctl -u mcp-server -f`
2. Test endpoint manually with curl
3. Verify token and authorization header
4. Check database connectivity and permissions

---

**Last Updated:** May 18, 2026  
**MCP Server Version:** Flask + Gunicorn  
**Database:** SQLite (brain.db)

# MCP Server VPS Deployment Guide

## Quick Start (Recommended)

Run this single command on your VPS as root:

```bash
cd /opt/my-website && bash deploy-mcp-systemd.sh
```

## Manual Steps (If you prefer to do it step-by-step)

### 1. SSH into your VPS
```bash
ssh root@103.97.127.67
```

### 2. Pull latest code
```bash
cd /opt/my-website
git pull
```

### 3. Create systemd service
```bash
sudo tee /etc/systemd/system/mcp-server.service > /dev/null << 'EOF'
[Unit]
Description=MCP Server (Flask + Gunicorn)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/my-website
Environment="PATH=/opt/my-website/venv/bin"
Environment="MCP_TOKEN=secret-token"
ExecStart=/opt/my-website/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:3001 --timeout 30 --access-logfile - --error-logfile - mcp.server:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
```

### 4. Reload systemd and enable service
```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-server
```

### 5. Start the service
```bash
sudo systemctl start mcp-server
sleep 2
sudo systemctl status mcp-server
```

### 6. Test the MCP endpoint

**With authentication (should work):**
```bash
curl -s -X POST \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"get_order_summary","params":{}}' \
  http://127.0.0.1:3001/mcp
```

**Without token (should return 401 Unauthorized):**
```bash
curl -s http://127.0.0.1:3001/mcp
```

**View logs:**
```bash
journalctl -u mcp-server -f
```

---

## Service Management Commands

```bash
# Start
sudo systemctl start mcp-server

# Stop
sudo systemctl stop mcp-server

# Restart
sudo systemctl restart mcp-server

# Check status
sudo systemctl status mcp-server

# View live logs
sudo journalctl -u mcp-server -f
```

---

## Integration with goClaw

Once the MCP server is running on your VPS, configure goClaw to connect:

### MCP Server Details
- **Host:** 127.0.0.1 (internal only, accessed via SSH tunnel or VPS internal)
- **Port:** 3001
- **Protocol:** HTTP
- **Endpoint:** `http://127.0.0.1:3001/mcp`
- **Auth:** Bearer token in `Authorization` header
- **Token:** `secret-token` (from environment variable)

### If goClaw runs on a different machine:

You'll need to expose the MCP server externally. Options:

1. **SSH Tunnel (Recommended for security):**
   ```bash
   ssh -L 3001:127.0.0.1:3001 root@103.97.127.67
   # Then connect goClaw to http://localhost:3001/mcp
   ```

2. **Bind to all interfaces (Less secure - use firewall):**
   - Modify systemd: change `--bind 127.0.0.1:3001` to `--bind 0.0.0.0:3001`
   - Restart: `sudo systemctl restart mcp-server`
   - Firewall: Only allow from goClaw server IP

3. **Reverse proxy via Caddy (Recommended for production):**
   - Add to Caddyfile: 
     ```
     lehoai.com/mcp {
         reverse_proxy 127.0.0.1:3001 {
             header_up Authorization "Bearer secret-token"
         }
     }
     ```
   - Then: `https://lehoai.com/mcp`

---

## Troubleshooting

**Check if port 3001 is listening:**
```bash
netstat -tlnp | grep 3001
# or
ss -tlnp | grep 3001
```

**View error logs:**
```bash
journalctl -u mcp-server -n 50
```

**Test with verbose output:**
```bash
journalctl -u mcp-server -f &
curl -v -H "Authorization: Bearer secret-token" http://127.0.0.1:3001/mcp
```

**Restart if issues occur:**
```bash
sudo systemctl restart mcp-server
```

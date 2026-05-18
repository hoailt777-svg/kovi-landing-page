#!/bin/bash
# Deploy MCP server on VPS with systemd service
# Run this script on the VPS as root: bash deploy-mcp-systemd.sh

set -e

echo "=== MCP Server Deployment Script ==="
echo ""

# Step 1: Update repository
echo "[1/6] Pulling latest code from repository..."
cd /opt/my-website
git pull
echo "✓ Code pulled"
echo ""

# Step 2: Create systemd service file
echo "[2/6] Creating systemd service file..."
cat > /etc/systemd/system/mcp-server.service << 'EOF'
[Unit]
Description=MCP Server (Flask + Gunicorn)
After=network.target
Wants=mywebsite.service

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
echo "✓ Service file created at /etc/systemd/system/mcp-server.service"
echo ""

# Step 3: Reload systemd daemon
echo "[3/6] Reloading systemd daemon..."
systemctl daemon-reload
echo "✓ Daemon reloaded"
echo ""

# Step 4: Enable service (autostart on boot)
echo "[4/6] Enabling mcp-server service..."
systemctl enable mcp-server
echo "✓ Service enabled"
echo ""

# Step 5: Start service
echo "[5/6] Starting mcp-server service..."
systemctl start mcp-server
sleep 2
echo "✓ Service started"
echo ""

# Step 6: Verify service is running
echo "[6/6] Checking service status..."
systemctl status mcp-server || true
echo ""

# Test curl with auth
echo "=== Testing MCP endpoint with Bearer token ==="
sleep 1
curl -s -X POST \
  -H "Authorization: Bearer secret-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"get_order_summary","params":{}}' \
  http://127.0.0.1:3001/mcp | head -c 200
echo ""
echo ""

# Test without auth (should get 401)
echo "=== Testing unauthorized request (no token) ==="
curl -s -w "\nHTTP Status: %{http_code}\n" http://127.0.0.1:3001/mcp | head -c 100
echo ""
echo ""

echo "✓ Deployment complete!"
echo ""
echo "=== Service Management ==="
echo "Start service:   systemctl start mcp-server"
echo "Stop service:    systemctl stop mcp-server"
echo "Restart service: systemctl restart mcp-server"
echo "View logs:       journalctl -u mcp-server -f"
echo "Service status:  systemctl status mcp-server"

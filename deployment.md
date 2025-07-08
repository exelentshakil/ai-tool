# 🚀 Simple PM2 + Gunicorn Deployment Guide

## 📋 Prerequisites
- Python 3.8+
- Node.js 16+ (for PM2)
- Ubuntu/Debian/CentOS server

## 🔧 Step 1: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install Node.js and npm
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install PM2 globally
sudo npm install -g pm2
```

## 📁 Step 2: Setup Project

```bash
# Create project directory
sudo mkdir -p /var/www/calculator-system
cd /var/www/calculator-system

# Set ownership (replace 'ubuntu' with your username)
sudo chown -R ubuntu:ubuntu /var/www/calculator-system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install flask==3.0.0 flask-cors==4.0.0 flask-limiter==3.5.0
pip install python-dotenv==1.0.0 openai==1.3.8 tinydb==4.8.0
pip install gunicorn==21.2.0 psutil==5.9.6

# Create required directories
mkdir -p config utils routes tools backups
touch utils/__init__.py routes/__init__.py tools/__init__.py
```

## ⚙️ Step 3: Create Environment File

```bash
# Create .env file
cat > .env << 'EOF'
OPENAI_API_KEY=your_openai_api_key_here
DAILY_OPENAI_BUDGET=50
MONTHLY_OPENAI_BUDGET=500
HOURLY_FREE_LIMIT=3
DAILY_FREE_LIMIT=10
HOURLY_BASIC_LIMIT=20
RESET_MINUTE=0
ADMIN_KEY=your-secure-admin-key-here
PREMIUM_IPS=127.0.0.1
PORT=5000
FLASK_ENV=production
EOF

# Secure the environment file
chmod 600 .env
```

## 📝 Step 4: Create Gunicorn Startup Script

```bash
# Create gunicorn startup script
cat > start_gunicorn.sh << 'EOF'
#!/bin/bash
cd /var/www/calculator-system
source venv/bin/activate
exec gunicorn \
    --bind 127.0.0.1:5000 \
    --workers 4 \
    --worker-class sync \
    --worker-connections 1000 \
    --max-requests 1000 \
    --max-requests-jitter 50 \
    --timeout 30 \
    --keep-alive 2 \
    --log-level info \
    --access-logfile /var/www/calculator-system/logs/access.log \
    --error-logfile /var/www/calculator-system/logs/error.log \
    app:app
EOF

# Make script executable
chmod +x start_gunicorn.sh

# Create logs directory
mkdir -p logs
```

## 🚀 Step 5: Start with PM2

```bash
# Start the application with PM2
pm2 start start_gunicorn.sh --name "calculator-api" --interpreter bash

# Check status
pm2 status

# View logs
pm2 logs calculator-api

# Monitor in real-time
pm2 monit
```

## 🔄 Step 6: Auto-Start on Boot

```bash
# Generate PM2 startup script
pm2 startup

# Copy and run the generated command (it will look like this):
# sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u ubuntu --hp /home/ubuntu

# Save current PM2 processes
pm2 save

# Test reboot (optional)
# sudo reboot
# pm2 status  # Should show your app running after reboot
```

## 🌐 Step 7: Setup Nginx (Optional but Recommended)

```bash
# Install Nginx
sudo apt install nginx -y

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/calculator-system << 'EOF'
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # Optional: Serve static files directly
    location /static/ {
        alias /var/www/calculator-system/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/calculator-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 📊 Step 8: Essential PM2 Commands

```bash
# Application Management
pm2 start calculator-api        # Start app
pm2 stop calculator-api         # Stop app
pm2 restart calculator-api      # Restart app
pm2 reload calculator-api       # Zero-downtime reload
pm2 delete calculator-api       # Remove app from PM2

# Monitoring
pm2 status                      # Show all apps status
pm2 logs calculator-api         # Show logs
pm2 logs calculator-api --lines 100  # Show last 100 log lines
pm2 monit                       # Real-time monitoring

# Process Information
pm2 describe calculator-api     # Detailed app info
pm2 list                        # List all processes

# Memory and Performance
pm2 flush calculator-api        # Clear logs
pm2 reset calculator-api        # Reset restart counter
```

## 🔧 Step 9: Health Check and Testing

```bash
# Test the API directly
curl http://localhost:5000/health

# Test through Nginx (if configured)
curl http://your-domain.com/health

# Expected response:
# {"status": "healthy", "tools_loaded": 0, ...}

# Test a calculator endpoint
curl -X POST http://localhost:5000/process-tool \
  -H "Content-Type: application/json" \
  -d '{"tool": "test-calculator", "data": {"value": 100}}'
```

## 📈 Step 10: Performance Optimization

```bash
# Update PM2 with performance settings
pm2 delete calculator-api

# Start with optimized settings
pm2 start start_gunicorn.sh \
  --name "calculator-api" \
  --interpreter bash \
  --max-memory-restart 500M \
  --max-restarts 10 \
  --min-uptime 10s

# Save the new configuration
pm2 save
```

## 🚨 Troubleshooting

### Check Application Status
```bash
# PM2 status
pm2 status

# Check logs for errors
pm2 logs calculator-api --err

# Check system resources
pm2 monit

# Restart if needed
pm2 restart calculator-api
```

### Check Ports and Processes
```bash
# Check if port 5000 is in use
sudo netstat -tulpn | grep :5000

# Check gunicorn processes
ps aux | grep gunicorn

# Check Nginx status (if using)
sudo systemctl status nginx
```

### Fix Common Issues
```bash
# Permission issues
sudo chown -R ubuntu:ubuntu /var/www/calculator-system

# Python path issues
cd /var/www/calculator-system
source venv/bin/activate
which python
which gunicorn

# Restart everything
pm2 restart calculator-api
sudo systemctl reload nginx
```

## 🔒 Security Hardening

```bash
# Create dedicated user (recommended)
sudo useradd -r -s /bin/false calculator
sudo chown -R calculator:calculator /var/www/calculator-system

# Update PM2 to run as calculator user
pm2 delete calculator-api
sudo -u calculator pm2 start /var/www/calculator-system/start_gunicorn.sh --name "calculator-api"

# Set up firewall (if needed)
sudo ufw allow 22    # SSH
sudo ufw allow 80    # HTTP
sudo ufw allow 443   # HTTPS
sudo ufw enable
```

## 📋 Quick Commands Reference

```bash
# Deploy new version
cd /var/www/calculator-system
git pull origin main  # or copy new files
source venv/bin/activate
pip install -r requirements.txt
pm2 reload calculator-api

# View real-time logs
pm2 logs calculator-api --lines 50 -f

# Emergency restart
pm2 restart calculator-api

# Check system health
pm2 monit
curl http://localhost:5000/health
```

## 🎯 Success Indicators

✅ `pm2 status` shows your app as "online"  
✅ `curl http://localhost:5000/health` returns JSON response  
✅ Logs show no errors: `pm2 logs calculator-api`  
✅ App auto-restarts on reboot  
✅ Memory usage is stable in `pm2 monit`  

Your calculator system is now running in production with PM2 + Gunicorn! 🚀

## 📞 Quick Support Commands

```bash
# Full system status
echo "=== PM2 Status ==="
pm2 status
echo "=== Last 20 Logs ==="
pm2 logs calculator-api --lines 20
echo "=== Health Check ==="
curl -s http://localhost:5000/health | python3 -m json.tool
echo "=== System Resources ==="
free -h && df -h
```
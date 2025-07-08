# 🚀 Optimized PM2 + Gunicorn Deployment for AI Tools

## 📋 Prerequisites
- Python 3.8+
- Node.js 16+ (for PM2)
- Ubuntu/Debian/CentOS server
- Git

## 🔧 Step 1: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install python3 python3-pip python3-venv git nginx curl -y

# Install Node.js and PM2
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
sudo npm install -g pm2
```

## 📁 Step 2: Clone and Setup Project

```bash
# Create project directory
sudo mkdir -p /var/www/ai-tools
cd /var/www/ai-tools

# Set ownership (replace 'ubuntu' with your username)
sudo chown -R ubuntu:ubuntu /var/www/ai-tools

# Clone your repository
git clone https://github.com/exelentshakil/ai-tool.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies from requirements.txt
pip install -r requirements.txt

# Install additional production dependencies
pip install gunicorn psutil
```

## ⚙️ Step 3: Production Environment Configuration

```bash
# Create production .env file
cat > .env << 'EOF'
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
DAILY_OPENAI_BUDGET=50
MONTHLY_OPENAI_BUDGET=500

# Rate Limiting
HOURLY_FREE_LIMIT=5
DAILY_FREE_LIMIT=15
HOURLY_PREMIUM_LIMIT=100
DAILY_PREMIUM_LIMIT=500

# Security
ADMIN_KEY=your-secure-admin-key-here
FLASK_SECRET_KEY=your-super-secret-flask-key-here

# Performance
WORKERS=4
MAX_REQUESTS=1000
TIMEOUT=60

# Environment
FLASK_ENV=production
PORT=5000
HOST=127.0.0.1

# Premium Features
PREMIUM_IPS=127.0.0.1,your.premium.ip.here
ENABLE_FACE_ANALYSIS=true
ENABLE_ADVANCED_FEATURES=true
EOF

# Secure the environment file
chmod 600 .env
```

## 🚀 Step 4: Optimized Gunicorn Configuration

```bash
# Create gunicorn configuration file
cat > gunicorn.conf.py << 'EOF'
import os
import multiprocessing

# Server socket
bind = f"{os.getenv('HOST', '127.0.0.1')}:{os.getenv('PORT', '5000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000
timeout = int(os.getenv('TIMEOUT', 60))
keepalive = 2
max_requests = int(os.getenv('MAX_REQUESTS', 1000))
max_requests_jitter = 50

# Restart workers after this many requests, with up to 50 random jitter
preload_app = True

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190

# Logging
accesslog = "/var/www/ai-tools/logs/access.log"
errorlog = "/var/www/ai-tools/logs/error.log"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "ai-tools-api"

# Server mechanics
daemon = False
pidfile = "/var/www/ai-tools/logs/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/ssl/key"
# certfile = "/path/to/ssl/cert"
EOF

# Create startup script
cat > start_app.sh << 'EOF'
#!/bin/bash
cd /var/www/ai-tools
source venv/bin/activate

# Ensure logs directory exists
mkdir -p logs

# Start with gunicorn
exec gunicorn -c gunicorn.conf.py app:app
EOF

chmod +x start_app.sh

# Create logs directory
mkdir -p logs
```

## 📊 Step 5: PM2 Process Configuration

```bash
# Create PM2 ecosystem file for better management
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'ai-tools-api',
    script: './start_app.sh',
    interpreter: 'bash',
    cwd: '/var/www/ai-tools',
    
    // Performance
    instances: 1,
    exec_mode: 'fork',
    max_memory_restart: '512M',
    
    // Restart policy
    autorestart: true,
    max_restarts: 10,
    min_uptime: '10s',
    restart_delay: 4000,
    
    // Logs
    log_file: '/var/www/ai-tools/logs/pm2-combined.log',
    out_file: '/var/www/ai-tools/logs/pm2-out.log',
    error_file: '/var/www/ai-tools/logs/pm2-error.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true,
    
    // Environment
    env: {
      NODE_ENV: 'production',
      PYTHONUNBUFFERED: '1'
    },
    
    // Monitoring
    pmx: true,
    
    // Advanced features
    watch: false,
    ignore_watch: ['node_modules', 'logs', '*.log'],
    
    // Source control
    source_map_support: false,
    
    // Graceful shutdown
    kill_timeout: 5000,
    shutdown_with_message: true
  }]
};
EOF

# Start application with PM2
pm2 start ecosystem.config.js

# Check status
pm2 status
pm2 logs ai-tools-api --lines 20
```

## 🌐 Step 6: High-Performance Nginx Configuration

```bash
# Create optimized Nginx configuration
sudo tee /etc/nginx/sites-available/ai-tools << 'EOF'
upstream ai_tools_backend {
    server 127.0.0.1:5000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;  # Replace with your domain
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=face_analysis:10m rate=1r/s;
    
    # Main API endpoint
    location / {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://ai_tools_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
        
        # Cache control
        proxy_cache_bypass $http_upgrade;
    }
    
    # Special rate limiting for face analysis
    location /analyze-face-enhanced {
        limit_req zone=face_analysis burst=5 nodelay;
        
        proxy_pass http://ai_tools_backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Extended timeout for AI processing
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
        
        # Larger body size for image uploads
        client_max_body_size 10M;
    }
    
    # Health check endpoint (no rate limiting)
    location /health {
        proxy_pass http://ai_tools_backend;
        proxy_set_header Host $host;
        access_log off;
    }
    
    # Block sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    location ~ \.(env|ini|log)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;
}
EOF

# Enable the site
sudo ln -s /etc/nginx/sites-available/ai-tools /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 🔄 Step 7: Auto-Start and Monitoring

```bash
# Setup PM2 auto-start
pm2 startup
# Run the generated command (will look like):
# sudo env PATH=$PATH:/usr/bin /usr/lib/node_modules/pm2/bin/pm2 startup systemd -u ubuntu --hp /home/ubuntu

# Save current PM2 configuration
pm2 save

# Create health check script
cat > health_check.sh << 'EOF'
#!/bin/bash
HEALTH_URL="http://localhost:5000/health"
LOG_FILE="/var/www/ai-tools/logs/health_check.log"

# Check if service is responding
if curl -f -s "$HEALTH_URL" > /dev/null; then
    echo "$(date): Health check passed" >> "$LOG_FILE"
    exit 0
else
    echo "$(date): Health check failed - restarting service" >> "$LOG_FILE"
    pm2 restart ai-tools-api
    exit 1
fi
EOF

chmod +x health_check.sh

# Add to crontab for monitoring (every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /var/www/ai-tools/health_check.sh") | crontab -
```

## 📈 Step 8: Performance Optimization

```bash
# Create performance tuning script
cat > optimize_system.sh << 'EOF'
#!/bin/bash

# Increase file descriptor limits
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize network settings
sudo tee -a /etc/sysctl.conf << SYSCTL
# Network optimizations
net.core.somaxconn = 65536
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65536
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 60
net.ipv4.tcp_keepalive_probes = 10
SYSCTL

# Apply changes
sudo sysctl -p

echo "System optimization complete. Reboot recommended."
EOF

chmod +x optimize_system.sh
# Run optimization (optional)
# ./optimize_system.sh
```

## 🚀 Step 9: Quick Deployment Script

```bash
# Create deployment script for updates
cat > deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Run any database migrations or setup
echo "🔧 Running setup..."
# python setup.py # Uncomment if you have setup scripts

# Restart application with zero downtime
echo "🔄 Restarting application..."
pm2 reload ai-tools-api

# Health check
sleep 5
echo "🏥 Health check..."
if curl -f -s http://localhost:5000/health > /dev/null; then
    echo "✅ Deployment successful!"
    pm2 logs ai-tools-api --lines 10
else
    echo "❌ Health check failed!"
    pm2 logs ai-tools-api --lines 20
    exit 1
fi
EOF

chmod +x deploy.sh
```

## 📊 Step 10: Essential Management Commands

```bash
# Quick status check
alias ai-status='pm2 status && curl -s http://localhost:5000/health | python3 -m json.tool'

# View logs
alias ai-logs='pm2 logs ai-tools-api'

# Restart service
alias ai-restart='pm2 restart ai-tools-api'

# Deploy updates
alias ai-deploy='cd /var/www/ai-tools && ./deploy.sh'

# Full system check
alias ai-check='cd /var/www/ai-tools && ./health_check.sh && nginx -t && pm2 monit'
```

## 🔒 Step 11: Security Hardening

```bash
# Create dedicated user (recommended for production)
sudo useradd -r -m -s /bin/bash aitools
sudo usermod -aG www-data aitools

# Set proper permissions
sudo chown -R aitools:www-data /var/www/ai-tools
sudo chmod -R 755 /var/www/ai-tools
sudo chmod 600 /var/www/ai-tools/.env

# Setup UFW firewall
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

echo "🔒 Security hardening complete"
```

## 🎯 Quick Verification

```bash
# Run this after deployment
cd /var/www/ai-tools

echo "=== System Status ==="
pm2 status

echo "=== Health Check ==="
curl -s http://localhost:5000/health | python3 -m json.tool

echo "=== Recent Logs ==="
pm2 logs ai-tools-api --lines 10

echo "=== Nginx Status ==="
sudo nginx -t

echo "=== Performance ==="
ps aux | grep -E "(gunicorn|nginx)" | grep -v grep
```

## 📞 Troubleshooting Commands

```bash
# Emergency restart
pm2 restart ai-tools-api && sudo systemctl reload nginx

# Check all processes
ps aux | grep -E "(python|gunicorn|nginx)" | grep -v grep

# View all logs
tail -f /var/www/ai-tools/logs/*.log

# Reset everything
pm2 delete ai-tools-api
pm2 start ecosystem.config.js
pm2 save

# Check disk space and memory
df -h && free -h
```

## ✅ Success Indicators

- ✅ `pm2 status` shows "online" status
- ✅ `curl http://localhost:5000/health` returns JSON with tools count
- ✅ Face analysis endpoint responds: `curl -X POST http://localhost:5000/analyze-face-enhanced`
- ✅ No errors in logs: `pm2 logs ai-tools-api --lines 50`
- ✅ App survives reboot test
- ✅ Nginx serves requests without errors

Your AI Tools API is now running optimally in production! 🚀

**Performance Features:**
- ⚡ Gunicorn with optimized worker configuration
- 🌐 Nginx with rate limiting and caching
- 📊 PM2 with auto-restart and monitoring
- 🔄 Zero-downtime deployments
- 🎯 Health checks and auto-recovery
- 🔒 Security hardening included
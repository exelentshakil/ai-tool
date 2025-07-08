# ⚡ **Super Quick Setup for ~/ai-tool**

## 🚀 **One-Time Setup (5 minutes)**

```bash
cd ~/ai-tool

# 1. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn pm2

# 2. Create production .env
cp .env .env.production  # Edit this with real values
nano .env.production

# 3. Create PM2 config
cat > ecosystem.config.js << 'EOF'
module.exports = {
  apps: [{
    name: 'ai-tools-api',
    script: 'gunicorn',
    args: '-b 127.0.0.1:5000 -w 4 app:app',
    cwd: '/home/ubuntu/ai-tool',
    interpreter: 'python',
    interpreter_args: '/home/ubuntu/ai-tool/venv/bin/python'
  }]
};
EOF

# 4. Start with PM2
npm install -g pm2
pm2 start ecosystem.config.js
pm2 save
pm2 startup

# 5. Check it's working
pm2 status
curl http://localhost:5000/health
```

## 🔄 **Future Deployments (30 seconds)**

```bash
cd ~/ai-tool

# Pull updates & restart
git stash
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
pm2 reload ai-tools-api

# Check status
curl http://localhost:5000/health
```

## 📊 **Quick Commands**
```bash
pm2 status           # Check status
pm2 logs ai-tools-api # View logs
pm2 restart ai-tools-api # Restart
```

That's it! Your API will be running on `http://localhost:5000` 🚀
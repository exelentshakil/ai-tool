#  Calculator System - Setup Instructions

## 📋 Prerequisites

- Python 3.8+ installed
- Node.js (optional, for local development)
- Git (for version control)

## 🔧 Installation Steps

### 1. Create Project Environment

```bash
# Create project directory
mkdir enhanced-calculator-system
cd enhanced-calculator-system

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

### 2. Install Python Dependencies

```bash
# Install all required packages
pip install -r requirements.txt

# Verify installation
pip list
```

### 3. Create Environment Configuration

Create a `.env` file in your project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Budget Limits
DAILY_OPENAI_BUDGET=50
MONTHLY_OPENAI_BUDGET=500

# Rate Limiting
HOURLY_FREE_LIMIT=3
DAILY_FREE_LIMIT=10
HOURLY_BASIC_LIMIT=20
RESET_MINUTE=0

# Admin Security
ADMIN_KEY=your-secret-admin-key-change-this

# Premium Users (comma-separated IPs)
PREMIUM_IPS=127.0.0.1,192.168.1.100

# Server Configuration
PORT=5000
FLASK_ENV=development
```

### 4. Create Directory Structure

```bash
# Create required directories
mkdir -p config utils routes tools backups

# Create empty __init__.py files
touch utils/__init__.py
touch routes/__init__.py
touch tools/__init__.py
```

### 5. Create Tools Configuration

Create `tools_config.json`:

```json
{
  "personal-injury-calculator": {
    "slug": "personal-injury-calculator",
    "category": "legal",
    "base_name": "Personal Injury Calculator",
    "variation": "calculator",
    "rpm": 45,
    "seo_data": {
      "title": "AI Personal Injury Calculator - Free Legal Calculator",
      "description": "Free AI-powered personal injury calculator. Get instant legal estimates, compare options, and find qualified attorneys.",
      "keywords": "personal injury calculator, legal calculator, settlement calculator",
      "h1": "AI-Powered Personal Injury Calculator",
      "focus_keyword": "personal injury calculator"
    }
  },
  "mortgage-calculator": {
    "slug": "mortgage-calculator",
    "category": "finance",
    "base_name": "Mortgage Calculator",
    "variation": "calculator",
    "rpm": 35,
    "seo_data": {
      "title": "Mortgage Calculator - Free Home Loan Calculator",
      "description": "Calculate monthly mortgage payments, compare rates, and find the best home loan options.",
      "keywords": "mortgage calculator, home loan calculator, monthly payment",
      "h1": "Smart Mortgage Calculator",
      "focus_keyword": "mortgage calculator"
    }
  }
}
```

## 🏃‍♂️ Running the Application

### Development Mode

```bash
# Start the Flask development server
python app.py

# Or with Flask CLI
export FLASK_APP=app.py
flask run
```

### Production Mode

```bash
# Using Gunicorn (Linux/Mac)
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Using Waitress (Windows)
waitress-serve --host=0.0.0.0 --port=5000 app:app
```

## 🔍 Testing the Installation

### 1. Health Check

Visit: `http://localhost:5000/health`

Expected response:
```json
{
  "status": "healthy",
  "tools_loaded": 2,
  "daily_ai_cost": 0,
  "budget_remaining": 50,
  "timestamp": "2025-01-08T..."
}
```

### 2. Test API Endpoint

```bash
curl -X POST http://localhost:5000/process-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "personal-injury-calculator",
    "data": {
      "case_type": "Personal Injury",
      "complexity": "Moderate",
      "location": "New York",
      "urgency": "High"
    }
  }'
```

### 3. Admin Dashboard

Visit: `http://localhost:5000/admin/stats`

Headers: `X-Admin-Key: your-secret-admin-key-change-this`

## 📊 Monitoring and Logs

### View Application Logs

```bash
# Real-time logs
tail -f app.log

# Or check console output during development
```

### Database Files Created

- `cache.json` - API response cache
- `analytics.json` - Usage analytics
- `api_usage.json` - API usage tracking
- `openai_costs.json` - OpenAI API costs
- `user_limits.json` - Rate limiting data

## 🔒 Security Considerations

### 1. Change Default Keys

```bash
# Generate secure admin key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Environment Variables

Never commit `.env` file to version control:

```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.json" >> .gitignore  # Database files
echo "__pycache__/" >> .gitignore
echo "venv/" >> .gitignore
```

### 3. Production Settings

For production deployment:

```bash
# Set environment variables
export FLASK_ENV=production
export OPENAI_API_KEY=your_production_key
export ADMIN_KEY=your_secure_admin_key
```

## 🌐 Frontend Integration

### Add JavaScript to Your HTML

```html
<!-- Required CDN Dependencies -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

<!-- Your Calculator Script -->
<script src="path/to/enhanced-calculator-system.js"></script>

<!-- Tool Configuration -->
<script>
const TOOL_CONFIG = {
  "slug": "your-tool-slug",
  "category": "finance", // or legal, health, business, etc.
  "base_name": "Your Calculator Name",
  "seo_data": {
    "title": "Your Calculator Title",
    "description": "Your calculator description"
  }
};
</script>
```

## 🚨 Troubleshooting

### Common Issues

1. **ModuleNotFoundError**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **OpenAI API Errors**
   - Check your API key is valid
   - Verify you have credits available
   - Check rate limits

3. **Database Permission Errors**
   ```bash
   chmod 755 .
   chmod 644 *.json
   ```

4. **Port Already in Use**
   ```bash
   # Find and kill process using port 5000
   lsof -ti:5000 | xargs kill -9
   # Or use different port
   export PORT=8000
   ```

### Logs and Debugging

```bash
# Enable debug mode
export FLASK_DEBUG=1

# Verbose logging
export FLASK_LOG_LEVEL=DEBUG
```

## 📈 Performance Optimization

### 1. Redis for Caching (Optional)

```bash
# Install Redis
# Ubuntu/Debian:
sudo apt-get install redis-server

# Mac:
brew install redis

# Start Redis
redis-server
```

### 2. Database Optimization

```bash
# Regular maintenance script
python -c "
from utils.database import clean_old_cache, optimize_all_databases
clean_old_cache(24)
optimize_all_databases()
"
```

## 🎯 Next Steps

1. **Customize Tools** - Add your specific calculator configurations
2. **Styling** - Modify CSS to match your brand
3. **Analytics** - Set up Google Analytics tracking
4. **Monitoring** - Implement error tracking (Sentry, etc.)
5. **Scaling** - Consider load balancing for high traffic

## 📞 Support

- Check logs in console output
- Verify all environment variables are set
- Test with simple curl commands first
- Monitor database file creation and growth

Your enhanced calculator system is now ready for production! 🚀
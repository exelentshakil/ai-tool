import os
from dotenv import load_dotenv

load_dotenv()

# ─── API CONFIGURATION ──────────────────────────────────────────────────────────
API_KEY = os.getenv("OPENAI_API_KEY")

# ─── BUDGET CONFIGURATION ───────────────────────────────────────────────────────
DAILY_OPENAI_BUDGET = float(os.getenv("DAILY_OPENAI_BUDGET", "50"))
MONTHLY_OPENAI_BUDGET = float(os.getenv("MONTHLY_OPENAI_BUDGET", "500"))

# ─── RATE LIMITING CONFIGURATION ────────────────────────────────────────────────
HOURLY_FREE_LIMIT = int(os.getenv("HOURLY_FREE_LIMIT", "3"))
DAILY_FREE_LIMIT = int(os.getenv("DAILY_FREE_LIMIT", "10"))
HOURLY_BASIC_LIMIT = int(os.getenv("HOURLY_BASIC_LIMIT", "20"))
RESET_MINUTE = int(os.getenv("RESET_MINUTE", "0"))

# ─── ADMIN CONFIGURATION ────────────────────────────────────────────────────────
ADMIN_KEY = os.getenv('ADMIN_KEY', 'your-secret-admin-key')

# ─── PREMIUM USER CONFIGURATION ─────────────────────────────────────────────────
PREMIUM_IPS = os.getenv("PREMIUM_IPS", "").split(",")

# ─── DATABASE FILES ─────────────────────────────────────────────────────────────
DB_FILES = {
    'cache': 'cache.json',
    'analytics': 'analytics.json',
    'usage': 'api_usage.json',
    'cost': 'openai_costs.json',
    'user_limits': 'user_limits.json'
}

# ─── TOOLS CONFIGURATION ────────────────────────────────────────────────────────
TOOLS_CONFIG_FILE = 'tools_config.json'

# ─── RESPONSE MODES ─────────────────────────────────────────────────────────────
class ResponseMode:
    FULL_AI = "full_ai"
    SMART_AI = "smart_ai"
    BASIC_AI = "basic_ai"
    CALC_ONLY = "calculator"
    RATE_LIMITED = "rate_limited"

# ─── MAIN CATEGORIES ────────────────────────────────────────────────────────────
MAIN_CATEGORIES = [
    'finance',
    'insurance',
    'health',
    'business',
    'legal',
    'real_estate',
    'tax',
    'retirement',
    'fitness',
    'nutrition'
]
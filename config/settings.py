import os
from dotenv import load_dotenv
import logging

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

SUPABASE_URL= os.getenv('SUPABASE_URL', 'your-secret-admin-key')
SUPABASE_KEY=os.getenv('SUPABASE_KEY', 'your-secret-admin-key')

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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Log Supabase configuration status
if SUPABASE_URL and SUPABASE_KEY:
    logger.info("✅ Supabase configuration loaded successfully")
    logger.info(
        f"📍 Supabase URL: {SUPABASE_URL[:50]}..." if len(SUPABASE_URL) > 50 else f"📍 Supabase URL: {SUPABASE_URL}")
else:
    logger.error("❌ Supabase configuration missing!")
    logger.error("Please add these to your .env file:")
    logger.error("SUPABASE_URL=your_supabase_project_url")
    logger.error("SUPABASE_KEY=your_supabase_anon_key")

# ─── OPENAI CONFIGURATION ───────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DAILY_OPENAI_BUDGET = os.getenv('DAILY_OPENAI_BUDGET', 0.0)
MONTHLY_OPENAI_BUDGET = os.getenv('MONTHLY_OPENAI_BUDGET', 0.0)

if OPENAI_API_KEY:
    logger.info("✅ OpenAI API key loaded successfully")
else:
    logger.error("❌ OpenAI API key missing!")
    logger.error("Please add OPENAI_API_KEY to your .env file")

# ─── RATE LIMITING CONFIGURATION ────────────────────────────────────────────
HOURLY_FREE_LIMIT = int(os.getenv('HOURLY_FREE_LIMIT', '50'))
RESET_MINUTE = int(os.getenv('RESET_MINUTE', '0'))

# Premium IP addresses (comma-separated in .env)
PREMIUM_IPS_STR = os.getenv('PREMIUM_IPS', '')
PREMIUM_IPS = [ip.strip() for ip in PREMIUM_IPS_STR.split(',') if ip.strip()] if PREMIUM_IPS_STR else []

# ─── FLASK CONFIGURATION ────────────────────────────────────────────────────
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# ─── CORS CONFIGURATION ─────────────────────────────────────────────────────
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

# ─── ADMIN CONFIGURATION ────────────────────────────────────────────────────
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')

# ─── LOGGING CONFIGURATION ──────────────────────────────────────────────────
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


# ─── VALIDATION ─────────────────────────────────────────────────────────────
def validate_configuration():
    """Validate all required configuration"""
    errors = []
    warnings = []

    # Required configurations
    if not SUPABASE_URL:
        errors.append("SUPABASE_URL is required")
    if not SUPABASE_KEY:
        errors.append("SUPABASE_KEY is required")
    if not OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY is required")

    # Optional but recommended
    if SECRET_KEY == 'your-secret-key-here':
        warnings.append("SECRET_KEY should be changed from default")
    if ADMIN_PASSWORD == 'admin123':
        warnings.append("ADMIN_PASSWORD should be changed from default")

    # Log results
    if errors:
        logger.error("❌ Configuration errors found:")
        for error in errors:
            logger.error(f"  - {error}")
        return False

    if warnings:
        logger.warning("⚠️ Configuration warnings:")
        for warning in warnings:
            logger.warning(f"  - {warning}")

    logger.info("✅ Configuration validation passed")
    return True


# ─── ENVIRONMENT INFO ───────────────────────────────────────────────────────
def get_environment_info():
    """Get environment information for debugging"""
    return {
        'flask_env': FLASK_ENV,
        'debug': DEBUG,
        'supabase_configured': bool(SUPABASE_URL and SUPABASE_KEY),
        'openai_configured': bool(OPENAI_API_KEY),
        'hourly_limit': HOURLY_FREE_LIMIT,
        'premium_ips_count': len(PREMIUM_IPS),
        'cors_origins': CORS_ORIGINS
    }


# Run validation on import
if __name__ == "__main__":
    print("🔍 Validating configuration...")
    validate_configuration()
    print("\n📋 Environment Info:")
    info = get_environment_info()
    for key, value in info.items():
        print(f"  {key}: {value}")
else:
    validate_configuration()
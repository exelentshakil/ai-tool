import re
from typing import Dict, Any
from decimal import Decimal, InvalidOperation


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert any value to float"""
    if value is None:
        return default

    try:
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = re.sub(r'[^\d.,\-+]', '', value.strip())
            if not cleaned:
                return default
            if cleaned.count(',') > 1:
                cleaned = cleaned.replace(',', '')
            elif ',' in cleaned and '.' in cleaned:
                comma_pos = cleaned.rfind(',')
                dot_pos = cleaned.rfind('.')
                if comma_pos > dot_pos:
                    cleaned = cleaned.replace('.', '').replace(',', '.')
                else:
                    cleaned = cleaned.replace(',', '')
            elif ',' in cleaned:
                parts = cleaned.split(',')
                if len(parts) == 2 and len(parts[1]) <= 3:
                    cleaned = cleaned.replace(',', '.')
                else:
                    cleaned = cleaned.replace(',', '')
            return float(cleaned)
    except (ValueError, TypeError, InvalidOperation):
        pass

    return default


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert any value to integer"""
    try:
        return int(safe_float(value, default))
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """Safely convert any value to string"""
    if value is None:
        return default
    return str(value).strip()


def validate_tool_inputs(user_data: Dict[str, Any], category: str) -> Dict[str, Any]:
    """Validate and clean tool inputs based on category"""
    cleaned = {}

    if category in ["business", "finance"]:
        cleaned["amount"] = safe_float(
            user_data.get("amount", user_data.get("revenue", user_data.get("loan_amount", 0))))
        cleaned["revenue"] = safe_float(user_data.get("revenue", user_data.get("annual_revenue", 0)))
        cleaned["expenses"] = safe_float(user_data.get("expenses", user_data.get("annual_expenses", 0)))
        cleaned["employees"] = safe_int(user_data.get("employees", 0))
        cleaned["industry"] = safe_str(user_data.get("industry", "Technology"))

    elif category == "insurance":
        cleaned["coverage_amount"] = safe_float(user_data.get("coverage_amount", user_data.get("amount", 100000)))
        cleaned["age"] = safe_int(user_data.get("age", 30))
        cleaned["location"] = safe_str(user_data.get("location", "National Average"))

    elif category == "real_estate":
        cleaned["home_price"] = safe_float(user_data.get("home_price", user_data.get("property_value", 400000)))
        cleaned["down_payment"] = safe_float(user_data.get("down_payment", 80000))
        cleaned["location"] = safe_str(user_data.get("location", "National Average"))

    elif category == "automotive":
        cleaned["vehicle_price"] = safe_float(user_data.get("vehicle_price", user_data.get("price", 35000)))
        cleaned["down_payment"] = safe_float(user_data.get("down_payment", 7000))
        cleaned["fuel_type"] = safe_str(user_data.get("fuel_type", "Gasoline"))

    elif category == "health":
        cleaned["height"] = safe_float(user_data.get("height", 68))
        cleaned["weight"] = safe_float(user_data.get("weight", 150))
        cleaned["age"] = safe_int(user_data.get("age", 30))

    elif category == "education":
        cleaned["tuition_cost"] = safe_float(user_data.get("tuition_cost", 25000))
        cleaned["years"] = safe_int(user_data.get("years", 4))
        cleaned["degree_type"] = safe_str(user_data.get("degree_type", "Bachelor's Degree"))

    elif category == "legal":
        cleaned["case_type"] = safe_str(user_data.get("case_type", "Business"))
        cleaned["complexity"] = safe_str(user_data.get("complexity", "Moderate"))
        cleaned["location"] = safe_str(user_data.get("location", "National Average"))

    else:
        # Generic validation for unknown categories
        for key, value in user_data.items():
            if isinstance(value, str) and any(char.isdigit() for char in value):
                cleaned[key] = safe_float(value)
            else:
                cleaned[key] = safe_str(value)

    return cleaned


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone):
    """Validate phone number format"""
    pattern = r'^\+?1?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$'
    return re.match(pattern, phone) is not None


def validate_url(url):
    """Validate URL format"""
    pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    return re.match(pattern, url) is not None


def sanitize_input(text, max_length=1000):
    """Sanitize text input"""
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', str(text))

    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."

    return text
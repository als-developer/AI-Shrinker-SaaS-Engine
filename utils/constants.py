"""
Global Constants - System-wide Configuration Constants
Version: 31.0
"""

# Exchange Rates (USD base)
EXCHANGE_RATES = {
    "USD": 1.0,
    "TZS": 2615.50,
    "KES": 132.20,
    "UGX": 3765.00,
    "RWF": 1280.00,
    "EUR": 0.92,
    "GBP": 0.78,
    "NGN": 1480.00,
    "ZAR": 18.50,
    "GHS": 12.80,
    "XOF": 600.00,
    "XAF": 600.00,
    "EGP": 48.00,
    "MAD": 10.00
}

# Cashback Configuration
CASHBACK_PERCENTAGE = 0.05  # 5% cashback on all transactions

# Rate Limit Profiles
RATE_LIMIT_PROFILES = {
    "free_tier": {"requests_per_minute": 10, "burst": 15, "daily_limit": 100},
    "developer_tier": {"requests_per_minute": 100, "burst": 150, "daily_limit": 5000},
    "business_tier": {"requests_per_minute": 1000, "burst": 1500, "daily_limit": 50000},
    "enterprise_tier": {"requests_per_minute": 5000, "burst": 7500, "daily_limit": 250000}
}

# Pricing Plans
PRICING_PLANS = {
    "free": {"price_usd": 0, "api_calls": 100, "support": "community"},
    "developer": {"price_usd": 49, "api_calls": 10000, "support": "priority"},
    "business": {"price_usd": 499, "api_calls": 100000, "support": "24/7"},
    "enterprise": {"price_usd": 2499, "api_calls": 1000000, "support": "dedicated"}
}

# Supported Languages
SUPPORTED_LANGUAGES = {
    "en": "English",
    "sw": "Kiswahili",
    "fr": "Français",
    "ar": "العربية",
    "es": "Español",
    "pt": "Português"
}

# Cache TTLs (seconds)
CACHE_TTL = {
    "short": 60,      # 1 minute
    "medium": 300,    # 5 minutes
    "long": 3600,     # 1 hour
    "day": 86400      # 24 hours
}

# Pagination Defaults
PAGINATION_DEFAULTS = {
    "page": 1,
    "per_page": 20,
    "max_per_page": 100
}

# HTTP Status Codes
HTTP_STATUS = {
    "OK": 200,
    "CREATED": 201,
    "ACCEPTED": 202,
    "NO_CONTENT": 204,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "TOO_MANY_REQUESTS": 429,
    "INTERNAL_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503
}

# Error Messages
ERROR_MESSAGES = {
    "unauthorized": "Authentication required. Please provide valid API key.",
    "forbidden": "Access denied. Insufficient permissions.",
    "not_found": "Resource not found.",
    "rate_limit": "Rate limit exceeded. Please slow down your requests.",
    "invalid_request": "Invalid request format.",
    "internal_error": "Internal server error. Please try again later.",
    "insufficient_credits": "Insufficient credits. Please top up your account."
}

# African Mobile Money Operators
MOBILE_MONEY_OPERATORS = {
    "mpesa": {"name": "M-Pesa", "countries": ["TZ", "KE", "UG", "RW"]},
    "tigo_pesa": {"name": "Tigo Pesa", "countries": ["TZ"]},
    "airtel_money": {"name": "Airtel Money", "countries": ["TZ", "KE", "UG", "MW", "ZM"]},
    "halopesa": {"name": "HaloPesa", "countries": ["TZ"]},
    "mtn_momo": {"name": "MTN MoMo", "countries": ["UG", "RW"]}
}

# Supported AI Models for Compression
SUPPORTED_AI_MODELS = {
    "meta-llama/Meta-Llama-3-70B": {"size_gb": 140, "architecture": "llama"},
    "meta-llama/Llama-2-70b": {"size_gb": 140, "architecture": "llama"},
    "mistralai/Mistral-7B-v0.1": {"size_gb": 14, "architecture": "mistral"},
    "meta-llama/Llama-2-7b": {"size_gb": 13.5, "architecture": "llama"},
    "tiiuae/falcon-40b": {"size_gb": 80, "architecture": "falcon"},
    "bigcode/starcoder": {"size_gb": 35, "architecture": "starcoder"}
}

# Default Admin Users
DEFAULT_ADMINS = [
    {"email": "admin@sovereigngrid.com", "role": "super_admin"},
    {"email": "support@sovereigngrid.com", "role": "support_admin"}
]

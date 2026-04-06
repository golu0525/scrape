"""
Configuration for ISP plan scraper
"""

import os
from datetime import datetime

# Database Configuration
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "isp_plans"),
    "port": int(os.getenv("DB_PORT", 3306)),
}

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
OUTPUT_PLANS_FILE = os.path.join(OUTPUT_DIR, "plans.json")
OUTPUT_LOGS_FILE = os.path.join(OUTPUT_DIR, "logs.json")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Provider Configurations
PROVIDERS = {
    "telstra": {
        "id": 1,
        "name": "Telstra",
        "api_url": "https://www.telstra.com.au/api/plans",  # Check actual API
        "web_url": "https://www.telstra.com.au/internet/nbn",
        "has_api": False,  # Set based on actual availability
    },
    "optus": {
        "id": 2,
        "name": "Optus",
        "api_url": "https://api.optus.com.au/plans",
        "web_url": "https://www.optus.com.au/network/nbn",
        "has_api": False,
    },
    "aussie": {
        "id": 3,
        "name": "Aussie Broadband",
        "api_url": "https://api.aussiebroadband.com.au/plans",
        "web_url": "https://www.aussiebroadband.com.au/broadband/nbn",
        "has_api": True,
    },
    "superloop": {
        "id": 4,
        "name": "Superloop",
        "api_url": "https://api.superloop.com.au/plans",
        "web_url": "https://www.superloop.com.au/nbn",
        "has_api": False,
    },
}

# Playwright Configuration
PLAYWRIGHT_CONFIG = {
    "headless": True,
    "timeout": 30000,  # 30 seconds
    "wait_selector_timeout": 10000,  # 10 seconds
}

# Retry Configuration
RETRY_CONFIG = {
    "max_retries": 3,
    "retry_delay": 2,  # seconds
}

# Request Headers
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Speed normalization (Mbps)
SPEED_UNITS = {
    "mbps": 1,
    "gbps": 1000,
    "kbps": 0.001,
}

# Network Types
NETWORK_TYPES = [
    "ADSL",
    "VDSL",
    "FTTC",
    "FTTN",
    "FTTP",
    "FIXED WIRELESS",
    "SATELLITE",
]

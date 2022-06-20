import logging
import os

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

# Meta-lookup
API_PORT = int(os.environ.get("PORT", 5057))

# Logging
LOG_LEVEL = getattr(logging, os.environ.get("LOG_LEVEL", "INFO"))
LOG_PATH = os.environ.get("LOG_PATH", None)

# Caching
ENABLE_CACHE = bool(os.environ.get("ENABLE_CACHE", True))
CACHE_DATABASE_URL = os.environ.get("CACHE_DATABASE_URL", "postgresql://metalookup:metalookup@postgres/metalookup")
ENABLE_CACHE_CONTROL_ENDPOINTS = bool(os.environ.get("ENABLE_CACHE_CONTROL_ENDPOINTS", True))

# Splash
SPLASH_URL = os.environ.get("SPLASH_URL", "http://splash:8050")
SPLASH_TIMEOUT = int(os.environ.get("SPLASH_TIMEOUT", 90))
SPLASH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
}

# Extractors
# Online lists
USE_LOCAL_IF_POSSIBLE = True

# Lighthouse
LIGHTHOUSE_URL = os.environ.get("LIGHTHOUSE_URL", "http://lighthouse:5058")
LIGHTHOUSE_TIMEOUT = int(os.environ.get("LIGHTHOUSE_TIMEOUT", 120))

# Miscellaneous
RETURN_IMAGES_IN_METADATA = False

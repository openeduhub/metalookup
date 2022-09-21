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
# Careful: in python bool("False") === True!
ENABLE_CACHE = os.environ.get("ENABLE_CACHE", "True") == "True"
CACHE_DATABASE_URL = os.environ.get("CACHE_DATABASE_URL", None)  # should never be used when ENABLE_CACHE is False.
ENABLE_CACHE_CONTROL_ENDPOINTS = os.environ.get("ENABLE_CACHE_CONTROL_ENDPOINTS", "True") == "True"
CACHE_WARMUP_CONCURRENCY = int(os.environ.get("CACHE_WARMUP_CONCURRENCY", 6))

# Playwright
PLAYWRIGHT_WS_ENDPOINT = os.environ.get("PLAYWRIGHT_WS_ENDPOINT", "ws://playwright:3000")
PLAYWRIGHT_PAGE_LOAD_TIMEOUT = int(os.environ.get("PLAYWRIGHT_PAGE_LOAD_TIMEOUT", 35))

# Extractors
# Online lists
USE_LOCAL_IF_POSSIBLE = True
# timeout in seconds for download of each of the addblock rule lists
ADBLOCK_DOWNLOAD_TIMEOUT = int(os.environ.get("ADBLOCK_DOWNLOAD_TIMEOUT", 300))

# Lighthouse
LIGHTHOUSE_URL = os.environ.get("LIGHTHOUSE_URL", "http://lighthouse:5058")
LIGHTHOUSE_TIMEOUT = int(os.environ.get("LIGHTHOUSE_TIMEOUT", 120))

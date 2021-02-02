import logging

API_PORT = 5057
LIGHTHOUSE_API_PORT = 5058

SPLASH_URL = "http://splash:8050"
SPLASH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
}

LOG_LEVEL = logging.DEBUG
LOG_PATH = "logs/"

# Online lists
USE_LOCAL_IF_POSSIBLE = True

# Miscellaneous
RETURN_IMAGES_IN_METADATA = False
API_RETRIES = 180

# Performance
WANT_PROFILING = False
VERSION = 0.2

import logging

from lib.constants import ACCESSIBILITY, SPLASH

API_PORT = 5057
LIGHTHOUSE_API_PORT = 5058
SPLASH_PORT = 8050

LOCALHOST_URL = "0.0.0.0"

USED_IN_PRODUCTION = True

if USED_IN_PRODUCTION:
    SPLASH_URL = f"http://{SPLASH}:{SPLASH_PORT}"
    ACCESSIBILITY_URL = f"http://{ACCESSIBILITY}:{LIGHTHOUSE_API_PORT}"
else:
    SPLASH_URL = f"http://{LOCALHOST_URL}:{SPLASH_PORT}"
    ACCESSIBILITY_URL = f"http://{LOCALHOST_URL}:{LIGHTHOUSE_API_PORT}"

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
VERSION = 1.0

# Tests
SKIP_E2E_TESTS = True

NUMBER_OF_EXTRACTORS = 22

# Database
if USED_IN_PRODUCTION:
    STORAGE_HOST_NAME = "db"
else:
    STORAGE_HOST_NAME = "localhost"

PROFILING_HOST_NAME = "local_record"

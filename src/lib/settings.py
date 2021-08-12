import logging

from lib.constants import ACCESSIBILITY, SPLASH

API_PORT = 5057
LIGHTHOUSE_API_PORT = 5058
SPLASH_PORT = 8050

SPLASH_URL = f"http://{SPLASH}:{SPLASH_PORT}"
ACCESSIBILITY_URL = f"http://{ACCESSIBILITY}:{LIGHTHOUSE_API_PORT}"

SPLASH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
}

LOG_LEVEL = logging.DEBUG
LOG_PATH = "logs/"

# Online lists
USE_LOCAL_IF_POSSIBLE = True
USE_RE2 = True

# Miscellaneous
RETURN_IMAGES_IN_METADATA = False
ACCESSIBILITY_TIMEOUT = 120
SPLASH_TIMEOUT = 90
API_RETRIES = max(180, ACCESSIBILITY_TIMEOUT * 2 + SPLASH_TIMEOUT)

# Performance
WANT_PROFILING = True
VERSION = 1.0

# Tests
SKIP_E2E_TESTS = True

NUMBER_OF_EXTRACTORS = 21

# Database
STORAGE_HOST_NAME = "db"

PROFILING_HOST_NAME = "local_record"

CACHE_RETENTION_TIME_DAYS = 4 * 7
MINIMUM_REQUIRED_ENTRIES = 5
BYPASS_CACHE = False

METALOOKUP_RECORDS = "https://metalookup.openeduhub.net/records"
METALOOKUP_EXTRACT_META = "https://metalookup.openeduhub.net/extract_meta"

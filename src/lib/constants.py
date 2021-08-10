from enum import Enum

MESSAGE_URL = "url"
MESSAGE_HTML = "html"
MESSAGE_HEADERS = "headers"
MESSAGE_ALLOW_LIST = "allow_list"
MESSAGE_META = "meta"
MESSAGE_EXCEPTION = "exception"
MESSAGE_HAR = "har"
MESSAGE_SHARED_MEMORY_NAME = "shared_memory_name"
MESSAGE_BYPASS_CACHE = "bypass_cache"

LOGFILE_MANAGER = "manager"

# Metadata

VALUES = "values"
PROBABILITY = "probability"
IS_HAPPY_CASE = "isHappyCase"
TIME_REQUIRED = "time_required"
EXPLANATION = "explanation"
TIMESTAMP = "timestamp"

ACCESSIBILITY = "accessibility"
SPLASH = "splash"
DESKTOP = "desktop"
MOBILE = "mobile"
SCORE = "score"
SCRIPT = "script"

METADATA_EXTRACTOR = "metadata_extractor"
LIGHTHOUSE_EXTRACTOR = "lighthouse_extractor"

# Header
STRICT_TRANSPORT_SECURITY = "strict-transport-security"

SECONDS_PER_DAY = 60 * 60 * 24


# Database
class ActionEnum(Enum):
    def __str__(self):
        return str(self.value)

    NONE = "none"
    RESPONSE = "response"
    REQUEST = "request"

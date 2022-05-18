import json
from pathlib import Path

from app.splash_models import SplashResponse


def test_splash_model():
    path = Path(__file__).parent.parent / "splash-response-google.json"
    with open(path, "r") as f:
        # just make sure we can parse it
        # if we can parse it, then the defined model hierarchy
        # complies with the example response and is ok.
        SplashResponse.parse_obj(json.load(f))

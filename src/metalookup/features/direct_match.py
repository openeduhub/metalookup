from concurrent.futures import Executor

from metalookup.app.models import Explanation, StarCase
from metalookup.core.content import Content
from metalookup.core.extractor import Extractor

_FOUND_LIST_MATCHES = "Found list matches"
_FOUND_NO_LIST_MATCHES = "Found no list matches"


class DirectMatch(Extractor[set[str]]):
    tag_list: list[str]

    def __init__(self):
        # normalize tag list, as we compare with lower case html content
        self.tag_list = sorted([tag.lower() for tag in self.tag_list])
        if len(self.tag_list) == 0:
            raise ValueError("Cannot use extractor with empty tag list")

    async def setup(self):
        pass

    async def extract(self, content: Content, executor: Executor) -> tuple[StarCase, Explanation, set[str]]:
        # fixme: html.lower() might be expensive but we do it multiple times (once for each of the derived classes)
        # fixme: eventually (if it turns out that below two lines regularly quite CPU heavy) move evaluation to
        #        executor and await
        html = (await content.html()).lower()
        matches = {ele for ele in self.tag_list if ele in html}

        explanation = _FOUND_LIST_MATCHES if len(matches) > 0 else _FOUND_NO_LIST_MATCHES
        stars = StarCase.ZERO if len(matches) > 0 else StarCase.FIVE

        return stars, explanation, matches


class Paywalls(DirectMatch):
    key = "paywall"
    tag_list = ["paywall", "paywalluser"]


class PopUp(DirectMatch):
    key = "pop_up"
    tag_list = [
        "popup",
        "popuptext",
        "modal",
        "modal fade",
        "modal-dialog",
        "interstitial",
        "Interstitial",
        "ToSeeWithEyesUncloudedByHate",
    ]


class RegWall(DirectMatch):
    key = "reg_wall"
    tag_list = [
        "regwall",
        "regiwall",
        "Regwall",
        "Regiwall",
        "register",
        "Register",
        "registration",
        "Registration",
        "registerbtn",
    ]


class LogInOut(DirectMatch):
    key = "log_in_out"
    tag_list = [
        "email",
        "psw",
        "Passwort",
        "password",
        "login",
        "Login",
        "logout",
        "Logout",
        "uname",
        "username",
        "submit",
        "Submit",
        "Username",
    ]

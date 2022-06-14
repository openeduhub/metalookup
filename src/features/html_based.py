from core.extractor import MetadataBase, ProbabilityDeterminationMethod


@MetadataBase.with_key(key="paywall")
class Paywalls(MetadataBase):
    tag_list = ["paywall", "paywalluser"]


@MetadataBase.with_key(key="iframe_embeddable")
class IFrameEmbeddable(MetadataBase):
    tag_list = ["X-Frame-Options"]
    evaluate_header = True
    decision_threshold = 0
    false_list = ["same-origin", "sameorigin", "deny"]
    probability_determination_method = ProbabilityDeterminationMethod.FALSE_LIST


@MetadataBase.with_key()
class PopUp(MetadataBase):
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


@MetadataBase.with_key()
class RegWall(MetadataBase):
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


@MetadataBase.with_key()
class LogInOut(MetadataBase):
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

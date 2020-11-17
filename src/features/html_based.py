from features.metadata_base import MetadataBase, ProbabilityDeterminationMethod


class Advertisement(MetadataBase):
    urls = [
        "https://easylist.to/easylist/easylist.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_adservers.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_adservers_popup.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_allowlist.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_allowlist_dimensions.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_allowlist_general_hide.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_allowlist_popup.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_general_block.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_general_block_dimensions.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_general_block_popup.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_general_hide.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_specific_block.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_specific_block_popup.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_specific_hide.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_thirdparty.txt",
        "https://github.com/easylist/easylist/blob/master/easylist/easylist_thirdparty_popup.txt",
    ]
    decision_threshold = 0
    probability_determination_method = (
        ProbabilityDeterminationMethod.NUMBER_OF_ELEMENTS
    )


class EasyPrivacy(MetadataBase):
    urls: list = [
        "https://easylist.to/easylist/easyprivacy.txt",
        "https://github.com/easylist/easylist/blob/master/easyprivacy/easyprivacy_general.txt",
        "https://github.com/easylist/easylist/blob/master/easyprivacy/easyprivacy_allowlist.txt",
        "https://github.com/easylist/easylist/blob/master/easyprivacy/easyprivacy_allowlist_international.txt",
        "https://github.com/easylist/easylist/blob/master/easyprivacy/easyprivacy_specific.txt",
        "https://github.com/easylist/easylist/blob/master/easyprivacy/easyprivacy_specific_international.txt",
        "https://github.com/easylist/easylist/blob/master/easyprivacy/easyprivacy_trackingservers.txt",
        "https://github.com/easylist/easylist/blob/master/easyprivacy/easyprivacy_trackingservers_international.txt",
        "https://github.com/easylist/easylist/blob/master/easyprivacy/easyprivacy_thirdparty.txt",
        "https://github.com/easylist/easylist/blob/master/easyprivacy/easyprivacy_thirdparty_international.txt",
    ]
    decision_threshold = 0


class IETracker(MetadataBase):
    url: str = "https://easylist-downloads.adblockplus.org/easyprivacy.tpl"
    key: str = "internet_explorer_tracker"
    comment_symbol = "#"
    decision_threshold = 0


class CookiesInHtml(MetadataBase):
    urls = [
        "https://easylist-downloads.adblockplus.org/easylist-cookie.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_cookie/easylist_cookie_allowlist.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_cookie/easylist_cookie_allowlist_general_hide.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_cookie/easylist_cookie_general_block.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_cookie/easylist_cookie_general_hide.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_cookie/easylist_cookie_international_specific_block.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_cookie/easylist_cookie_international_specific_hide.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_cookie/easylist_cookie_specific_block.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_cookie/easylist_cookie_specific_hide.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_cookie/easylist_cookie_thirdparty.txt",
    ]
    decision_threshold = 0


class FanboyAnnoyance(MetadataBase):
    urls = [
        "https://easylist.to/easylist/fanboy-annoyance.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_annoyance_allowlist.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_annoyance_allowlist_general_hide.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_annoyance_general_block.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_annoyance_general_hide.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_annoyance_international.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_annoyance_specific_block.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_annoyance_thirdparty.txt",
    ]
    decision_threshold = 0
    probability_determination_method = (
        ProbabilityDeterminationMethod.NUMBER_OF_ELEMENTS
    )


class FanboyNotification(MetadataBase):
    urls = [
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_notifications_allowlist.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_notifications_allowlist_general_hide.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_notifications_general_block.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_notifications_general_hide.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_notifications_specific_block.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_notifications_specific_hide.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_notifications_thirdparty.txt",
    ]
    decision_threshold = 0
    probability_determination_method = (
        ProbabilityDeterminationMethod.NUMBER_OF_ELEMENTS
    )


class FanboySocialMedia(MetadataBase):
    urls = [
        "https://easylist.to/easylist/fanboy-social.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_social_allowlist.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_social_allowlist_general_hide.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_social_general_block.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_social_general_hide.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_social_international.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_social_specific_block.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_social_specific_hide.txt",
        "https://github.com/easylist/easylist/blob/master/fanboy-addon/fanboy_social_thirdparty.txt",
    ]
    decision_threshold = 0


class AntiAdBlock(MetadataBase):
    urls: list = [
        "https://easylist-downloads.adblockplus.org/antiadblockfilters.txt",
        "https://github.com/easylist/antiadblockfilters/blob/master/antiadblockfilters/antiadblock_german.txt",
        "https://github.com/easylist/antiadblockfilters/blob/master/antiadblockfilters/antiadblock_english.txt",
    ]
    key: str = "anti_adblock"
    decision_threshold = 0


class EasylistGermany(MetadataBase):
    urls: list = [
        "https://easylist.to/easylistgermany/easylistgermany.txt",
        "https://github.com/easylist/easylistgermany/blob/master/easylistgermany/easylistgermany_adservers.txt",
        "https://github.com/easylist/easylistgermany/blob/master/easylistgermany/easylistgermany_adservers_popup.txt",
        "https://github.com/easylist/easylistgermany/blob/master/easylistgermany/easylistgermany_allowlist.txt",
        "https://github.com/easylist/easylistgermany/blob/master/easylistgermany/easylistgermany_allowlist_dimensions.txt",
        "https://github.com/easylist/easylistgermany/blob/master/easylistgermany/easylistgermany_allowlist_general_hide.txt",
        "https://github.com/easylist/easylistgermany/blob/master/easylistgermany/easylistgermany_allowlist_popup.txt",
        "https://github.com/easylist/easylistgermany/blob/master/easylistgermany/easylistgermany_general_block.txt",
        "https://github.com/easylist/easylistgermany/blob/master/easylistgermany/easylistgermany_general_block_popup.txt",
        "https://github.com/easylist/easylistgermany/blob/master/easylistgermany/easylistgermany_general_hide.txt",
        "https://github.com/easylist/easylistgermany/blob/master/easylistgermany/easylistgermany_specific_block.txt",
        "https://github.com/easylist/easylistgermany/blob/master/easylistgermany/easylistgermany_specific_block_popup.txt",
        "https://github.com/easylist/easylistgermany/blob/master/easylistgermany/easylistgermany_specific_hide.txt",
        "https://github.com/easylist/easylistgermany/blob/master/easylistgermany/easylistgermany_thirdparty.txt",
        "https://github.com/easylist/easylistgermany/blob/master/easylistgermany/easylistgermany_thirdparty_popup.txt",
    ]
    decision_threshold = 0


class EasylistAdult(MetadataBase):
    urls: list = [
        "https://github.com/easylist/easylist/blob/master/easylist_adult/adult_adservers.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_adult/adult_adservers_popup.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_adult/adult_allowlist.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_adult/adult_allowlist_popup.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_adult/adult_specific_block.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_adult/adult_specific_block_popup.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_adult/adult_specific_hide.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_adult/adult_thirdparty.txt",
        "https://github.com/easylist/easylist/blob/master/easylist_adult/adult_thirdparty_popup.txt",
    ]
    decision_threshold = 0


class Paywalls(MetadataBase):
    tag_list = ["paywall", "paywalluser"]
    key: str = "paywall"
    decision_threshold = 0


class ContentSecurityPolicy(MetadataBase):
    tag_list = ["Content-Security-Policy"]
    evaluate_header = True


class IFrameEmbeddable(MetadataBase):
    tag_list = ["X-Frame-Options"]
    key: str = "iframe_embeddable"
    evaluate_header = True
    decision_threshold = 0


class PopUp(MetadataBase):
    tag_list = [
        "popup",
        "popuptext",
        "modal",
        "modal fade",
        "modal-dialog",
        "interstitial",
        "Interstitial",
    ]
    decision_threshold = 0


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

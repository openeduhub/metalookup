from metadata import Metadata


class Advertisement(Metadata):
    url: str = "https://easylist.to/easylist/easylist.txt"
    key: str = "ads"
    comment_symbol = "!"


class Tracker(Metadata):
    url: str = "https://easylist.to/easylist/easyprivacy.txt"
    key: str = "tracker"
    comment_symbol = "!"


class IETracker(Metadata):
    url: str = "https://easylist-downloads.adblockplus.org/easyprivacy.tpl"
    key: str = "internet_explorer_tracker"
    comment_symbol = "#"


class Cookies(Metadata):
    url: str = "https://easylist-downloads.adblockplus.org/easylist-cookie.txt"
    key: str = "cookies"
    comment_symbol = "!"


class EasylistGermany(Metadata):
    url: str = "https://easylist.to/easylistgermany/easylistgermany.txt"
    key: str = "easylist_germany"
    comment_symbol = "!"


class FanboyAnnoyance(Metadata):
    url: str = "https://easylist.to/easylist/fanboy-annoyance.txt"
    key: str = "fanboy_annoyance"
    comment_symbol = "!"


class FanboySocialMedia(Metadata):
    url: str = "https://easylist.to/easylist/fanboy-social.txt"
    key: str = "fanboy_social"
    comment_symbol = "!"


class AntiAdBlock(Metadata):
    url: str = "https://easylist-downloads.adblockplus.org/antiadblockfilters.txt"
    key: str = "anti_adblock"
    comment_symbol = "!"


class Paywalls(Metadata):
    tag_list = ["paywall", "paywalluser"]
    key: str = "paywall"


class ContentSecurityPolicy(Metadata):
    tag_list = ["Content-Security-Policy"]
    key: str = "content_security_policy"
    evaluate_header = True


class IFrameEmbeddable(Metadata):
    tag_list = ["X-Frame-Options"]
    key: str = "iframe_embeddable"
    evaluate_header = True

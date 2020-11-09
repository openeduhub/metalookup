from features.metadata_base import MetadataBase


class Advertisement(MetadataBase):
    urls = [
        "https://easylist.to/easylist/easylist.txt",
        "https://easylist.to/easylist/easylist_adservers.txt",
        "https://easylist.to/easylist/easylist_adservers_popup.txt",
        "https://easylist.to/easylist/easylist_allowlist.txt",
        "https://easylist.to/easylist/easylist_allowlist_dimensions.txt",
        "https://easylist.to/easylist/easylist_allowlist_general_hide.txt",
        "https://easylist.to/easylist/easylist_allowlist_popup.txt",
        "https://easylist.to/easylist/easylist_general_block.txt",
        "https://easylist.to/easylist/easylist_general_block_dimensions.txt",
        "https://easylist.to/easylist/easylist_general_block_popup.txt",
        "https://easylist.to/easylist/easylist_general_hide.txt",
        "https://easylist.to/easylist/easylist_specific_block.txt",
        "https://easylist.to/easylist/easylist_specific_block_popup.txt",
        "https://easylist.to/easylist/easylist_specific_hide.txt",
        "https://easylist.to/easylist/easylist_thirdparty.txt",
        "https://easylist.to/easylist/easylist_thirdparty_popup.txt",
    ]


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


class IETracker(MetadataBase):
    url: str = "https://easylist-downloads.adblockplus.org/easyprivacy.tpl"
    key: str = "internet_explorer_tracker"
    comment_symbol = "#"


class Cookies(MetadataBase):
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


class FanboyAnnoyance(MetadataBase):
    urls = [
        "https://easylist.to/easylist/fanboy-annoyance.txt",
        "https://easylist.to/easylist/fanboy_annoyance_allowlist.txt",
        "https://easylist.to/easylist/fanboy_annoyance_allowlist_general_hide.txt",
        "https://easylist.to/easylist/fanboy_annoyance_general_block.txt",
        "https://easylist.to/easylist/fanboy_annoyance_general_hide.txt",
        "https://easylist.to/easylist/fanboy_annoyance_international.txt",
        "https://easylist.to/easylist/fanboy_annoyance_specific_block.txt",
        "https://easylist.to/easylist/fanboy_annoyance_thirdparty.txt",
    ]


class FanboyNotification(MetadataBase):
    urls = [
        "https://easylist.to/easylist/fanboy_notifications_allowlist.txt",
        "https://easylist.to/easylist/fanboy_notifications_allowlist_general_hide.txt",
        "https://easylist.to/easylist/fanboy_notifications_general_block.txt",
        "https://easylist.to/easylist/fanboy_notifications_general_hide.txt",
        "https://easylist.to/easylist/fanboy_notifications_specific_block.txt",
        "https://easylist.to/easylist/fanboy_notifications_specific_hide.txt",
        "https://easylist.to/easylist/fanboy_notifications_thirdparty.txt",
    ]


class FanboySocialMedia(MetadataBase):
    urls = [
        "https://easylist.to/easylist/fanboy-social.txt",
        "https://easylist.to/easylist/fanboy_social_allowlist.txt",
        "https://easylist.to/easylist/fanboy_social_allowlist_general_hide.txt",
        "https://easylist.to/easylist/fanboy_social_general_block.txt",
        "https://easylist.to/easylist/fanboy_social_general_hide.txt",
        "https://easylist.to/easylist/fanboy_social_international.txt",
        "https://easylist.to/easylist/fanboy_social_specific_block.txt",
        "https://easylist.to/easylist/fanboy_social_specific_hide.txt",
        "https://easylist.to/easylist/fanboy_social_thirdparty.txt",
    ]


class AntiAdBlock(MetadataBase):
    urls: list = [
        "https://easylist-downloads.adblockplus.org/antiadblockfilters.txt",
        "https://github.com/easylist/antiadblockfilters/blob/master/antiadblockfilters/antiadblock_german.txt",
        "https://github.com/easylist/antiadblockfilters/blob/master/antiadblockfilters/antiadblock_english.txt",
    ]
    key: str = "anti_adblock"


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


class Paywalls(MetadataBase):
    tag_list = ["paywall", "paywalluser"]
    key: str = "paywall"


class ContentSecurityPolicy(MetadataBase):
    tag_list = ["Content-Security-Policy"]
    evaluate_header = True


class IFrameEmbeddable(MetadataBase):
    tag_list = ["X-Frame-Options"]
    key: str = "iframe_embeddable"
    evaluate_header = True


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

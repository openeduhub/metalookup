from core.metadata_base import (
    ExtractionMethod,
    MetadataBase,
    ProbabilityDeterminationMethod,
)


@MetadataBase.with_key()
class Advertisement(MetadataBase):
    urls = [
        "https://easylist.to/easylist/easylist.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_adservers.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_adservers_popup.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_allowlist.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_allowlist_dimensions.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_allowlist_general_hide.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_allowlist_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_general_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_general_block_dimensions.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_general_block_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_specific_block_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_thirdparty.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist/easylist_thirdparty_popup.txt",
    ]
    call_async = True
    extraction_method = ExtractionMethod.USE_ADBLOCK_PARSER


@MetadataBase.with_key()
class EasyPrivacy(MetadataBase):
    urls: list = [
        "https://easylist.to/easylist/easyprivacy.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_general.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_allowlist.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_allowlist_international.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_specific.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_specific_international.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_trackingservers.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_trackingservers_international.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_thirdparty.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easyprivacy/easyprivacy_thirdparty_international.txt",
    ]
    call_async = True
    extraction_method = ExtractionMethod.USE_ADBLOCK_PARSER


@MetadataBase.with_key()
class FanboyAnnoyance(MetadataBase):
    urls = [
        "https://easylist.to/easylist/fanboy-annoyance.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_annoyance_allowlist.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_annoyance_allowlist_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_annoyance_general_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_annoyance_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_annoyance_international.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_annoyance_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_annoyance_thirdparty.txt",
    ]
    call_async = True
    extraction_method = ExtractionMethod.USE_ADBLOCK_PARSER


@MetadataBase.with_key()
class FanboyNotification(MetadataBase):
    urls = [
        # "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_notifications_allowlist.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_notifications_allowlist_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_notifications_general_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_notifications_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_notifications_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_notifications_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_notifications_thirdparty.txt",
    ]
    call_async = True
    extraction_method = ExtractionMethod.USE_ADBLOCK_PARSER


@MetadataBase.with_key()
class FanboySocialMedia(MetadataBase):
    urls = [
        "https://easylist.to/easylist/fanboy-social.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_allowlist.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_allowlist_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_general_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_international.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/fanboy-addon/fanboy_social_thirdparty.txt",
    ]
    call_async = True
    extraction_method = ExtractionMethod.USE_ADBLOCK_PARSER


@MetadataBase.with_key(key="anti_adblock")
class AntiAdBlock(MetadataBase):
    urls: list = [
        "https://easylist-downloads.adblockplus.org/antiadblockfilters.txt",
        "https://raw.githubusercontent.com/easylist/antiadblockfilters/master/antiadblockfilters/antiadblock_german.txt",
        "https://raw.githubusercontent.com/easylist/antiadblockfilters/master/antiadblockfilters/antiadblock_english.txt",
    ]
    key: str = "anti_adblock"
    extraction_method = ExtractionMethod.USE_ADBLOCK_PARSER


@MetadataBase.with_key()
class EasylistGermany(MetadataBase):
    urls: list = [
        "https://easylist.to/easylistgermany/easylistgermany.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_adservers.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_adservers_popup.txt",
        # "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_allowlist.txt",
        # "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_allowlist_dimensions.txt",
        # "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_allowlist_general_hide.txt",
        # "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_allowlist_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_general_block.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_general_block_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_general_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_specific_block_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_thirdparty.txt",
        "https://raw.githubusercontent.com/easylist/easylistgermany/master/easylistgermany/easylistgermany_thirdparty_popup.txt",
    ]
    call_async = True
    extraction_method = ExtractionMethod.USE_ADBLOCK_PARSER


@MetadataBase.with_key()
class EasylistAdult(MetadataBase):
    urls: list = [
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_adservers.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_adservers_popup.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_allowlist.txt",
        # "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_allowlist_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_specific_block.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_specific_block_popup.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_specific_hide.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_thirdparty.txt",
        "https://raw.githubusercontent.com/easylist/easylist/master/easylist_adult/adult_thirdparty_popup.txt",
    ]
    call_async = True
    extraction_method = ExtractionMethod.USE_ADBLOCK_PARSER


@MetadataBase.with_key(key="paywall")
class Paywalls(MetadataBase):
    tag_list = ["paywall", "paywalluser"]


@MetadataBase.with_key(key="iframe_embeddable")
class IFrameEmbeddable(MetadataBase):
    tag_list = ["X-Frame-Options"]
    evaluate_header = True
    decision_threshold = 0
    false_list = ["same-origin", "sameorigin", "deny"]
    probability_determination_method = (
        ProbabilityDeterminationMethod.FALSE_LIST
    )


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

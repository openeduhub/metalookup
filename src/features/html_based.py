from metadata import Metadata


class Advertisement(Metadata):
    url: str = "https://easylist.to/easylist/easylist.txt"
    key: str = "ads"
    comment_symbol = "!"


class Tracker(Metadata):
    url: str = "https://easylist.to/easylist/easyprivacy.txt"
    key: str = "tracker"
    comment_symbol = "!"


class ContentSecurityPolicy(Metadata):
    url: str = ""
    tag_list = ["Content-Security-Policy"]
    key: str = "content_security_policy"
    comment_symbol = "!"
    evaluate_header = True


class IFrameEmbeddable(Metadata):
    url: str = ""
    tag_list = ["X-Frame-Options"]
    key: str = "iframe_embeddable"
    comment_symbol = "!"
    evaluate_header = True

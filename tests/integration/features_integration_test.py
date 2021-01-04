from features.html_based import Advertisement
from features.website_manager import WebsiteData, WebsiteManager
from lib.logger import create_logger

# TODO Check other features, e.g. adult:
# html = {
#     "html": "9content.com\n,ytimm.com\n,boyzshop.com/affimages/",
#     "har": "",
#     "url": "",
# }
# expected = {
#     "easylist_adult": {
#         "values": ["9content.com", "ad_slot="],
#         "runs_within": 10,  # time the evaluation may take AT MAX -> acceptance test}
#     }
# }


def test_advertisement(mocker):
    _logger = create_logger()

    advertisement = Advertisement(_logger)

    advertisement.setup()
    website_manager = WebsiteManager.get_instance()

    html = {
        "html": "<script src='/xlayer/layer.php?uid='></script>",
        "har": "",
        "url": "",
        "headers": "{}",
    }
    expected = {
        "advertisement": {
            "values": ["/xlayer/layer.php?uid=$script"],
            "runs_within": 10,  # time the evaluation may take AT MAX -> acceptance test
        },
    }

    website_manager.load_raw_data(html)

    data = advertisement.start()

    website_manager.reset()

    assert (
        data["advertisement"]["values"] == expected["advertisement"]["values"]
    )
    runs_fast_enough = (
        data["advertisement"]["time_required"]
        <= expected["advertisement"]["runs_within"]
    )
    assert runs_fast_enough

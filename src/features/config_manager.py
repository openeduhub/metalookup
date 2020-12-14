from features.website_manager import Singleton
from lib.constants import DECISION, PROBABILITY, VALUES

# FIXME: Dummy config, move to file if there are a lot of entries
HOST_SPECIFIC_CONFIG = {
    "bbc": {
        "advertisement": {VALUES: [], PROBABILITY: 1.0, DECISION: False},
        "iframe_embeddable": {
            VALUES: ["test_shennanigan"],
            PROBABILITY: 1.0,
            DECISION: False,
        },
    },
    "github": {
        "advertisement": {
            VALUES: ["random_ads"],
            PROBABILITY: 1.0,
            DECISION: False,
        },
        "iframe_embeddable": {
            VALUES: ["test_shenanigan"],
            PROBABILITY: 1.0,
            DECISION: False,
        },
    },
}


@Singleton
class ConfigManager:
    def __init__(self):
        super().__init__()
        self.hosts: dict = HOST_SPECIFIC_CONFIG
        self.top_level_domain: str = ""

    def is_host_predefined(self):
        return self.top_level_domain in self.hosts.keys()

    def is_metadata_predefined(self, key: str):
        return (
            key in self.hosts[self.top_level_domain].keys()
            if self.top_level_domain != ""
            else False
        )

    def get_predefined_metadata(self, key: str) -> dict:
        return {key: self.hosts[self.top_level_domain][key]}

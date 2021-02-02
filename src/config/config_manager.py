import json

from features.website_manager import Singleton


@Singleton
class ConfigManager:
    def __init__(self):
        super().__init__()
        self.top_level_domain: str = ""
        self._load_config()

    def _load_config(self) -> None:
        with open("config/config.json", "r") as json_file:
            text = "".join(json_file.readlines())
            self.hosts: dict = json.loads(text)

    def is_host_predefined(self) -> bool:
        return self.top_level_domain in self.hosts.keys()

    def is_metadata_predefined(self, key: str) -> bool:
        return (
            key in self.hosts[self.top_level_domain].keys()
            if self.top_level_domain != ""
            else False
        )

    def get_predefined_metadata(self, key: str) -> dict:
        return {key: self.hosts[self.top_level_domain][key]}

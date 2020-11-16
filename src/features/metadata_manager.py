from config_manager import ConfigManager
from features.extract_from_document import ExtractFromFiles
from features.html_based import (
    Advertisement,
    AntiAdBlock,
    ContentSecurityPolicy,
    Cookies,
    EasylistAdult,
    EasylistGermany,
    EasyPrivacy,
    FanboyAnnoyance,
    FanboyNotification,
    FanboySocialMedia,
    IETracker,
    IFrameEmbeddable,
    Paywalls,
    PopUp,
)
from features.malicious_extensions import MaliciousExtensions
from features.metadata_base import MetadataBase
from features.website_manager import Singleton, WebsiteManager
from lib.constants import (
    MESSAGE_ALLOW_LIST,
    MESSAGE_HEADERS,
    MESSAGE_HTML,
    MESSAGE_URL,
)
from lib.logger import create_logger
from lib.timing import get_utc_now


@Singleton
class MetadataManager:
    metadata_extractors: list = []

    def __init__(self):
        self._logger = create_logger()

    def _create_extractors(self) -> None:

        extractors = [
            Advertisement,
            EasyPrivacy,
            MaliciousExtensions,
            ExtractFromFiles,
            IETracker,
            Cookies,
            FanboyAnnoyance,
            FanboyNotification,
            FanboySocialMedia,
            AntiAdBlock,
            EasylistGermany,
            EasylistAdult,
            Paywalls,
            ContentSecurityPolicy,
            IFrameEmbeddable,
            PopUp,
        ]

        for extractor in extractors:
            self.metadata_extractors.append(extractor(self._logger))

    def _setup_extractors(self) -> None:
        for metadata_extractor in self.metadata_extractors:
            metadata_extractor: MetadataBase
            metadata_extractor.setup()

    def setup(self) -> None:
        self._create_extractors()
        self._setup_extractors()

    def _extract_meta_data(
        self, allow_list: dict, config_manager: ConfigManager
    ) -> dict:
        data = {}
        for metadata_extractor in self.metadata_extractors:
            if allow_list[metadata_extractor.key]:
                if (
                    config_manager.is_host_predefined()
                    and config_manager.is_metadata_predefined(
                        metadata_extractor.key
                    )
                ):
                    extracted_metadata = (
                        config_manager.get_predefined_metadata(
                            metadata_extractor.key
                        )
                    )
                else:
                    extracted_metadata = metadata_extractor.start()

                data.update(extracted_metadata)
                self._logger.debug(f"Resulting data: {data}")
        return data

    def start(self, message: dict) -> dict:

        website_manager = WebsiteManager.get_instance()
        website_manager.load_raw_data(
            url=message[MESSAGE_URL],
            html_content=message[MESSAGE_HTML],
            raw_header=message[MESSAGE_HEADERS],
        )

        config_manager = ConfigManager.get_instance()
        config_manager.top_level_domain = (
            website_manager.website_data.top_level_domain
        )

        starting_extraction = get_utc_now()
        try:
            extracted_meta_data = self._extract_meta_data(
                message[MESSAGE_ALLOW_LIST], config_manager
            )
        except Exception as e:
            self._logger.exception(
                f"Extracting metadata raised: '{e.args}'",
                exc_info=True,
            )
            extracted_meta_data = {}

        extracted_meta_data.update(
            {
                "time_for_extraction": get_utc_now() - starting_extraction,
                **website_manager.get_website_data_to_log(),
            }
        )

        website_manager.reset()
        return extracted_meta_data

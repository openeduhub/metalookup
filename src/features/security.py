from app.models import StarCase, Explanation
from features.metadata_base import MetadataBase
from features.website_manager import WebsiteData
from lib.constants import STRICT_TRANSPORT_SECURITY, VALUES


class Security(MetadataBase):
    decision_threshold = 0.99

    expected_headers: dict = {
        "cache-control": {0: ["no-cache", "no-store"]},
        "content-security-policy": {},
        "referrer-policy": {},
        STRICT_TRANSPORT_SECURITY: {0: ["max-age=", "includeSubDomains"]},
        "x-content-type-options": {0: ["nosniff"]},
        "x-frame-options": {0: ["deny", "same_origin"]},
        "x-xss-protection": {
            0: ["1"],
            1: ["mode=block"],
        },
    }

    @staticmethod
    def _unify_text(text: str) -> str:
        return text.replace("_", "").replace("-", "").lower()

    def _start(self, website_data: WebsiteData) -> dict:
        values = []

        for tag, expected_value in self.expected_headers.items():
            if tag in website_data.headers:
                if len(expected_value) == 0:
                    values.append(tag)
                else:

                    header_value = self._extract_header_values(
                        website_data.headers[tag]
                    )

                    expected_value = self._process_expected_values(
                        expected_value
                    )

                    found_keys = self._number_of_expected_keys_in_header(
                        expected_value, header_value
                    )

                    if (
                        tag == STRICT_TRANSPORT_SECURITY
                        and self._is_sts_mag_age_greater_than_zero(
                            header_value
                        )
                    ):
                        found_keys += 1

                    if found_keys == len(expected_value.keys()):
                        values.append(tag)

        return {VALUES: values}

    def _extract_header_values(self, header: list) -> list:
        header_value = [
            self._unify_text(value).replace(",", ";").split(";")
            for value in header
        ]
        return [el for val in header_value for el in val]

    def _process_expected_values(self, expected_value: dict) -> dict:
        for idx, element in expected_value.items():
            expected_value.update(
                {int(idx): [self._unify_text(value) for value in element]}
            )
        return expected_value

    @staticmethod
    def _number_of_expected_keys_in_header(
        expected_value: dict, header_value: list
    ) -> int:
        found_values = sum(
            [
                1
                for value in expected_value.values()
                for val in value
                if val in header_value
            ]
        )
        return found_values

    @staticmethod
    def _is_sts_mag_age_greater_than_zero(header_value: list) -> bool:
        greater_than_zero = False
        for el in header_value:
            if el.startswith("maxage=") and int(el.split("=")[-1]) > 0:
                greater_than_zero = True
        return greater_than_zero

    def _decide(
        self, website_data: WebsiteData
    ) -> tuple[StarCase,  list[Explanation]]:
        probability = len(website_data.values) / len(
            self.expected_headers.keys()
        )
        decision = self._get_inverted_decision(probability)
        explanation = (
            [Explanation.MinimumSecurityRequirementsCovered]
            if decision == StarCase.FIVE
            else [Explanation.IndicatorsForInsufficientSecurityFound]
        )
        return decision, explanation

import contextlib
import io
import typing
from concurrent.futures import Executor
from pathlib import Path
from unittest import mock

import pytest
from aiohttp import ClientSession

from features.extract_from_files import ExtractFromFiles
from tests.integration.features_integration_test import mock_website_data


@contextlib.contextmanager
def file_download_mock():
    """Patch the ExtractFromFiles download method to instead load the files from the test resources."""

    async def download_mock(self, file_url: str, session: ClientSession) -> typing.BinaryIO:
        filename = file_url.split("/")[-1]
        with open(Path(__file__).parent.parent / "resources" / filename, "rb") as f:
            return io.BytesIO(f.read())

    with mock.patch("features.extract_from_files.ExtractFromFiles._download_file", download_mock):
        yield


@pytest.mark.asyncio
async def test_extract_from_files(executor: Executor):
    feature = ExtractFromFiles()
    await feature.setup()

    html = """<a href=\"https://dummy.wirlernenonline.de/arbeitsblatt_analog_losung.pdf\" target=\"_blank\">
           Arbeitsblatt analog L\u00f6sung.pdf</a>
           <a href=\"https://dummy.wirlernenonline.de/arbeitsblatt_analog_losung.docx\" target=\"_blank\">
           Arbeitsblatt analog L\u00f6sung.docx</a>
           """
    site = await mock_website_data(html=html)

    extractable = ExtractFromFiles._get_extractable_files(site)
    assert extractable == {
        "https://dummy.wirlernenonline.de/arbeitsblatt_analog_losung.pdf",
        "https://dummy.wirlernenonline.de/arbeitsblatt_analog_losung.docx",
    }

    with file_download_mock():
        stars, explanation, extra = await feature.extract(site, executor=executor)
        assert extra == {
            "https://dummy.wirlernenonline.de/arbeitsblatt_analog_losung.pdf",
            "https://dummy.wirlernenonline.de/arbeitsblatt_analog_losung.docx",
        }

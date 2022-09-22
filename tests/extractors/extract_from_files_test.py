import contextlib
import io
import typing
from concurrent.futures import Executor
from pathlib import Path
from unittest import mock

import pytest
from aiohttp import ClientSession

from metalookup.features.extract_from_files import ExtractFromFiles
from tests.extractors.conftest import mock_content


@contextlib.contextmanager
def file_download_mock():
    """Patch the ExtractFromFiles download method to instead load the files from the test resources."""

    async def download_mock(self, file_url: str, session: ClientSession) -> typing.BinaryIO:
        filename = file_url.split("/")[-1]
        with open(Path(__file__).parent.parent / "resources" / filename, "rb") as f:
            return io.BytesIO(f.read())

    with mock.patch("metalookup.features.extract_from_files.ExtractFromFiles._download_file", download_mock):
        yield


@pytest.mark.asyncio
async def test_extract_from_files(executor: Executor):
    feature = ExtractFromFiles()
    await feature.setup()

    html = """
    <a href="https://dummy.wirlernenonline.de/arbeitsblatt.pdf">
    Arbeitsblatt
    </a>
    <a href="/arbeitsblatt.docx"">
    Arbeitsblatt
    </a>
   """
    content = mock_content(html=html, url="https://dummy.wirlernenonline.de")

    extractable = await ExtractFromFiles._get_extractable_files(content)
    assert extractable == {
        "https://dummy.wirlernenonline.de/arbeitsblatt.pdf",
        "https://dummy.wirlernenonline.de/arbeitsblatt.docx",
    }

    with file_download_mock():
        stars, explanation, extra = await feature.extract(content, executor=executor)
        assert extra == {
            "https://dummy.wirlernenonline.de/arbeitsblatt.pdf",
            "https://dummy.wirlernenonline.de/arbeitsblatt.docx",
        }


@pytest.mark.asyncio
async def test_relative_url_download(executor: Executor):
    # Avoid regressions of https://github.com/openeduhub/metalookup/issues/118
    feature = ExtractFromFiles()
    await feature.setup()

    content = mock_content(
        html="""
             <a href="/link1.pdf">Arbeitsblatt</a>
             <a href="/foo/bar/link2.pdf">Arbeitsblatt</a>
             <a href="link3.pdf">Arbeitsblatt</a>
             """,
        url="https://dummy.wirlernenonline.de",
    )

    extractable = await ExtractFromFiles._get_extractable_files(content)
    assert extractable == {
        "https://dummy.wirlernenonline.de/link1.pdf",
        "https://dummy.wirlernenonline.de/foo/bar/link2.pdf",
        "https://dummy.wirlernenonline.de/link3.pdf",
    }

    content = mock_content(
        html="""
              <a href="/link1.pdf">Arbeitsblatt</a>
              <a href="/foo/bar/link2.pdf">Arbeitsblatt</a>
              <a href="link3.pdf">Arbeitsblatt</a>
              """,
        url="https://dummy.wirlernenonline.de/some/path",
    )

    extractable = await ExtractFromFiles._get_extractable_files(content)
    assert extractable == {
        "https://dummy.wirlernenonline.de/some/path/link1.pdf",
        "https://dummy.wirlernenonline.de/some/path/foo/bar/link2.pdf",
        "https://dummy.wirlernenonline.de/some/path/link3.pdf",
    }

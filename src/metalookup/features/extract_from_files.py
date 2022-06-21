import asyncio
import base64
import io
import logging
import os
import zipfile
from concurrent.futures import Executor
from typing import BinaryIO, Iterable, Optional
from urllib.parse import urlparse

import PyPDF2
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
from PyPDF2.errors import PdfReadError

from metalookup.app.models import Explanation, StarCase
from metalookup.core.extractor import Extractor
from metalookup.core.website_manager import WebsiteData
from metalookup.lib.settings import RETURN_IMAGES_IN_METADATA

logger = logging.getLogger(__file__)


_CONTENT_SIZE_THRESHOLD = 25  # if a downloaded content is larger than X megabytes it will not be analyzed
_NO_FILES_TO_EXTRACT = "No files to extract"
_SUFFICIENT_AMOUNT_OF_FILES_EXTRACTABLE = "Could extract content from most extractable files"
_INSUFFICIENT_AMOUNT_OF_FILES_EXTRACTABLE = "Could not extract content from the required fraction of extractable files"


class ExtractFromFiles(Extractor[set[str]]):
    key = "extract_from_files"

    threshold = 0.5
    """The fraction of files that need to be readable to yield a 5 star rating."""

    xmp_metadata = [
        "dc_contributor",
        "dc_coverage",
        "dc_creator",
        "dc_date",
        "dc_description",
        "dc_format",
        "dc_identifier",
        "dc_language",
        "dc_publisher",
        "dc_relation",
        "dc_rights",
        "dc_source",
        "dc_subject",
        "dc_title",
        "dc_type",
        "pdf_keywords",
        "pdf_pdfversion",
        "pdf_producer",
        "xmp_createDate",
        "xmp_modifyDate",
        "xmp_metadataDate",
        "xmp_creatorTool",
        "xmpmm_documentId",
        "xmpmm_instanceId",
    ]

    async def setup(self):
        pass

    async def extract(self, site: WebsiteData, executor: Executor) -> tuple[StarCase, Explanation, set[str]]:
        extractable_files = self._get_extractable_files(site)

        if len(extractable_files) == 0:  # avoid division by zero error below
            return StarCase.FIVE, _NO_FILES_TO_EXTRACT, set()

        values = await self._work_files(files=extractable_files, executor=executor)

        fraction = len(values) / len(extractable_files)
        explanation = (
            _SUFFICIENT_AMOUNT_OF_FILES_EXTRACTABLE
            if fraction >= self.threshold
            else _INSUFFICIENT_AMOUNT_OF_FILES_EXTRACTABLE
        )
        stars = StarCase.FIVE if fraction >= self.threshold else StarCase.ZERO
        return stars, explanation, values

    @staticmethod
    def _get_xml_body(soup: BeautifulSoup, xml_file: zipfile.ZipInfo) -> BeautifulSoup:
        body = BeautifulSoup()
        if xml_file.filename == "word/document.xml":
            body = soup.document.body
        elif xml_file.filename == "word/footer1.xml":
            body = soup.ftr
        elif xml_file.filename == "word/header1.xml":
            body = soup.hdr
        return body

    @staticmethod
    def _extract_xml_content(document: zipfile.ZipFile, xml_file: zipfile.ZipInfo) -> list:
        content = document.read(xml_file, pwd=None).decode()
        soup = BeautifulSoup(content, "xml")

        body = ExtractFromFiles._get_xml_body(soup, xml_file)
        return [tag.string for tag in body.find_all("t")]

    @staticmethod
    def _extract_image_content(document: zipfile.ZipFile, xml_file: zipfile.ZipInfo) -> dict:
        image = document.read(xml_file, pwd=None)
        image = base64.b64encode(image).decode()
        return {xml_file.filename: image}

    def _extract_docx(self, file: BinaryIO) -> tuple[list[str], dict[str, str]]:
        document = zipfile.ZipFile(file=file)

        extracted_content = []
        images = {}

        for file in document.filelist:
            if file.filename.find(".xml") >= 0:
                extracted_content += self._extract_xml_content(document, file)
            elif RETURN_IMAGES_IN_METADATA and file.filename.find("media") >= 0:
                images.update(self._extract_image_content(document, file))

        return extracted_content, images

    def _get_pdf_content(self, file: BinaryIO, pdf_file: PyPDF2.PdfFileReader) -> str:
        extracted_content = f"{pdf_file.metadata}"
        data = pdf_file.xmp_metadata
        for parameter in self.xmp_metadata:
            if parameter:
                try:
                    extracted_content += f"{parameter}, {getattr(data, parameter)}"
                except (AttributeError, TypeError) as err:
                    logger.exception(f"Parameter in pdf content failed to be retrieved: {parameter} with {err.args}")
        extracted_content += extract_text(file)
        return extracted_content

    @staticmethod
    def _get_pdf_images(reader: PyPDF2.PdfFileReader) -> list:
        resources_tag = "/Resources"
        xobject_tag = "/XObject"
        subtype_tag = "/Subtype"

        def images(x_object) -> Iterable[str]:
            for obj in x_object:
                if x_object[obj][subtype_tag] == "/Image":
                    yield obj

        def x_objects():
            for page in reader.pages:
                if resources_tag in page.keys() and xobject_tag in page[resources_tag].keys():
                    yield page[resources_tag][xobject_tag].get_object()

        return [image for x_object in x_objects() for image in images(x_object)]

    def _extract_pdfs(self, file: BinaryIO) -> tuple[str, list[str]]:
        try:
            pdf_file = PyPDF2.PdfFileReader(file)
            extracted_content = self._get_pdf_content(file, pdf_file)
            images = self._get_pdf_images(pdf_file)
            return extracted_content, images
        except (PdfReadError, OSError):
            return "", []

    async def _download_file(self, file: str, session: ClientSession) -> BinaryIO:
        result = await session.get(url=file)
        if result.status != 200:
            logger.exception(f"Downloading file '{file}' yielded status code '{result.status}'.")
        if result.content_length is not None and result.content_length > _CONTENT_SIZE_THRESHOLD * 1024 * 1024:
            logger.info(f"Skipping processing of full content for {file=} with {result.content_length=}")
            return io.BytesIO(b"<skipped>")
        return io.BytesIO(await result.read())

    def _process_file(self, file: BinaryIO, extension: str) -> bool:
        """
        Returns true whether some content could be extracted from the file.
        This function may be relatively CPU heavy and can hence be dispatched to an executor pool.
        """
        if extension == "docx":
            content, _ = self._extract_docx(file)
        elif extension == "pdf":
            content, _ = self._extract_pdfs(file)
        else:
            raise ValueError(f"Unsupported extension {extension}")

        return len(content) > 0

    async def _work_files(self, executor: Executor, files: list) -> set[str]:
        async with ClientSession() as session:

            async def task(url: str) -> Optional[str]:
                extension = os.path.basename(urlparse(url).path).split(".")[-1]
                if extension not in {"docx", "pdf"}:
                    return None

                file = await self._download_file(url, session)

                loop = asyncio.get_running_loop()
                success = await loop.run_in_executor(executor, self._process_file, file, extension)
                return url if success else None

            tasks = [task(url=file) for file in files]
            extractable_files: tuple[Optional[str], ...] = await asyncio.gather(*tasks)

        return {file for file in extractable_files if file is not None}

    @staticmethod
    def _get_extractable_files(website_data: WebsiteData) -> set[str]:
        file_extensions = [os.path.splitext(link)[-1] for link in website_data.raw_links]

        return {
            file for file, extension in zip(website_data.raw_links, file_extensions) if extension in [".docx", ".pdf"]
        }

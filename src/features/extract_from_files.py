import asyncio
import base64
import os
import zipfile
from urllib.parse import urlparse

import PyPDF2
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from pdfminer.high_level import extract_text
from PyPDF2.utils import PdfReadError

from app.models import Explanation, StarCase
from core.metadata_base import MetadataBase
from core.website_manager import WebsiteData
from lib.settings import RETURN_IMAGES_IN_METADATA


@MetadataBase.with_key()
class ExtractFromFiles(MetadataBase):
    decision_threshold = 0.5

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

    def _extract_docx(self, filename: str) -> dict:
        document = zipfile.ZipFile(filename)

        extracted_content = []
        images = {}

        for file in document.filelist:
            if file.filename.find(".xml") >= 0:
                extracted_content += self._extract_xml_content(document, file)
            elif RETURN_IMAGES_IN_METADATA and file.filename.find("media") >= 0:
                images.update(self._extract_image_content(document, file))

        return {"extracted_content": extracted_content, "images": images}

    def _get_pdf_content(self, filename: str, pdf_file: PyPDF2.PdfFileReader) -> str:
        extracted_content = f"{pdf_file.getDocumentInfo()}"
        data = pdf_file.getXmpMetadata()
        for parameter in self.xmp_metadata:
            if parameter:
                try:
                    extracted_content += f"{parameter}, {getattr(data, parameter)}"
                except (AttributeError, TypeError) as err:
                    self._logger.exception(
                        f"Parameter in pdf content failed to be retrieved: {parameter} with {err.args}"
                    )
        extracted_content += extract_text(filename)
        return extracted_content

    @staticmethod
    def _get_pdf_images(pdf_file: PyPDF2.PdfFileReader) -> list:
        images = []
        resources_tag = "/Resources"
        xobject_tag = "/XObject"
        subtype_tag = "/Subtype"
        for page in range(pdf_file.getNumPages()):
            pdf_page = pdf_file.getPage(page)
            if resources_tag in pdf_page.keys() and xobject_tag in pdf_page[resources_tag].keys():
                x_object = pdf_page[resources_tag][xobject_tag].getObject()

                for obj in x_object:
                    if x_object[obj][subtype_tag] == "/Image":
                        images += obj
        return images

    def _extract_pdfs(self, filename: str) -> dict:
        try:
            pdf_file = PyPDF2.PdfFileReader(open(filename, "rb"))
            extracted_content = self._get_pdf_content(filename, pdf_file)
            images = self._get_pdf_images(pdf_file)
        except (PdfReadError, OSError):
            extracted_content = []
            images = []

        return {"extracted_content": extracted_content, "images": images}

    async def _download_file(self, file_url: str, filename: str, session: ClientSession) -> None:
        result = await session.get(url=file_url)
        if result.status != 200:
            self._logger.exception(f"Downloading file '{file_url}' yielded status code '{result.status}'.")
        open(filename, "wb").write(await result.read())

    async def _process_file(self, file: str, session: ClientSession) -> str:
        filename = os.path.basename(urlparse(file).path)
        extension = filename.split(".")[-1]
        await self._download_file(file, filename, session)

        content = {"extracted_content": [], "images": {}}
        if extension == "docx":
            content = self._extract_docx(filename)
        elif extension == "pdf":
            content = self._extract_pdfs(filename)

        os.remove(filename)

        if len(content["extracted_content"]) == 0:
            filename = ""
        return filename

    async def _work_files(self, files: list) -> list[str]:
        async with ClientSession() as session:
            tasks = [self._process_file(file, session) for file in files]
            extractable_files = await asyncio.gather(*tasks)

        return [file for file in extractable_files if file != ""]

    @staticmethod
    def _get_extractable_files(website_data: WebsiteData) -> list:
        file_extensions = [os.path.splitext(link)[-1] for link in website_data.raw_links]

        extractable_files = [
            file for file, extension in zip(website_data.raw_links, file_extensions) if extension in [".docx", ".pdf"]
        ]

        return extractable_files

    async def _start(self, website_data: WebsiteData) -> list[str]:
        extractable_files = self._get_extractable_files(website_data)
        return await self._work_files(files=extractable_files)

    def _decide(self, website_data: WebsiteData) -> tuple[StarCase, list[Explanation]]:
        probability = 0
        extractable_files = self._get_extractable_files(website_data)

        if website_data.values:
            probability = len(extractable_files) / len(website_data.values)
        decision = self._get_inverted_decision(probability)
        explanation = (
            [Explanation.ExtractableFilesFound]
            if decision == StarCase.FIVE
            else [Explanation.InsufficientlyExtractableFilesFound]
        )
        return decision, explanation

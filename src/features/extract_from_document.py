import base64
import os
import zipfile
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from features.metadata_base import MetadataBase
from features.website_manager import WebsiteData
from lib.constants import VALUES


class ExtractFromFiles(MetadataBase):
    def _load_docx(self, docx, filename):
        result = requests.get(docx)
        if result.status_code == 200:
            self.tag_list = result.text.splitlines()
        else:
            self._logger.warning(
                f"Downloading tag list from '{docx}' yielded status code '{result.status_code}'."
            )

        open(filename, "wb").write(result.content)

    @staticmethod
    def _extract_docx(filename) -> dict:
        document = zipfile.ZipFile(filename)

        xml_files = document.filelist

        extracted_content = []
        images = {}

        for xml_file in xml_files:
            if xml_file.filename.find(".xml") >= 0:
                content = document.read(xml_file, pwd=None).decode()
                soup = BeautifulSoup(content, "xml")

                body = None
                if xml_file.filename == "word/document.xml":
                    body = soup.document.body
                elif xml_file.filename == "word/footer1.xml":
                    body = soup.ftr
                elif xml_file.filename == "word/header1.xml":
                    body = soup.hdr

                text_pieces = []
                if body:
                    text_pieces = [tag.string for tag in body.find_all("t")]

                extracted_content += text_pieces
            elif xml_file.filename.find("media") >= 0:
                image = document.read(xml_file, pwd=None)
                image = base64.b64encode(image).decode()

                images.update({xml_file.filename: image})

        content = {"content": extracted_content, "images": images}

        return content

    def _work_docx(self, docx_files):
        values = {VALUES: []}

        for file in docx_files:
            filename = os.path.basename(urlparse(file).path)
            self._load_docx(file, filename)
            content = self._extract_docx(filename)
            values.update({filename: content})
            values[VALUES].append(filename)
            os.remove(filename)

        return values

    def _start(self, website_data: WebsiteData) -> dict:

        file_extensions = [
            os.path.splitext(link)[-1] for link in website_data.raw_links
        ]

        docx_files = [
            file
            for file, extension in zip(website_data.raw_links, file_extensions)
            if extension == ".docx"
        ]

        values = self._work_docx(docx_files=docx_files)

        return {**values}

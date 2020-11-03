import os

from bs4 import BeautifulSoup

from features.MetadataBase import MetadataBase


class ExtractLinks(MetadataBase):
    key: str = "extracted_links"

    @staticmethod
    def __extract_raw_links(soup: BeautifulSoup) -> list:
        return list({a['href'] for a in soup.find_all(href=True)})

    @staticmethod
    def __extract_extensions(links: list):
        file_extensions = [os.path.splitext(link)[-1] for link in links]
        file_extensions = [x for x in list(set(file_extensions)) if x != ""]
        return file_extensions

    @staticmethod
    def __extract_images(soup: BeautifulSoup) -> list:
        # TODO: We only gather the url here. There is more information stored here!
        image_links = [image.attrs.get("src") for image in soup.findAll("img")]
        return image_links

    def _start(self, html_content: str, header: dict) -> list:
        soup = BeautifulSoup(html_content, 'html.parser')

        raw_links = self.__extract_raw_links(soup)
        image_links = self.__extract_images(soup)
        extensions = self.__extract_extensions(raw_links)

        # FIXME: This breaks the typing. How to resolve?
        return {"images": image_links, "extensions": extensions, "raw_links": raw_links}

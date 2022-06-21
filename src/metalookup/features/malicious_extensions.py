import os
from concurrent.futures import Executor
from urllib.parse import urlparse

from metalookup.app.models import Explanation, StarCase
from metalookup.core.extractor import Extractor
from metalookup.core.website_manager import WebsiteData

FOUND_POTENTIALLY_MALICIOUS_EXTENSION = "Found potentially malicious extension"
FOUND_SLIGHTLY_MALICIOUS_EXTENSION = "Found slightly malicious extension"
NO_DANGEROUS_EXTENSIONS_FOUND = "Found no malicious or dangerous extensions"


class MaliciousExtensions(Extractor[set[str]]):
    """
    Returns the set of extensions that lead to the given star rating, i.e. either the malicious extensions for a
    zero star rating, or the dangerous extensions for a four star rating. In case of a 5 star rating the set is empty.
    """

    key = "malicious_extensions"

    # Based on: https://www.file-extensions.org/filetype/extension/name/dangerous-malicious-files
    #           https://www.howtogeek.com/137270/50-file-extensions-that-are-potentially-dangerous-on-windows/
    #           https://sensorstechforum.com/file-types-used-malware-2019/
    #           https://www.howtogeek.com/127154/how-hackers-can-disguise-malicious-programs-with-fake-file-extensions/

    def __init__(self):
        self.dangerous_extensions = {".docx", ".js", ".pptx", ".html", ".pdf"}
        self.malicious_extensions = {
            ".msp",
            ".cfxxe",
            ".php3",
            ".vb",
            ".swf",
            ".mcq",
            ".dyv",
            ".ps1",
            ".9",
            ".ocx",
            ".chm",
            ".mshxml",
            ".lkh",
            ".hlp",
            ".iws",
            ".gadget",
            ".pr",
            ".wlpginstall",
            ".kcd",
            ".dom",
            ".hsq",
            ".aepl",
            ".0_full_0_tgod_signed",
            ".dyz",
            ".psc1",
            ".py",
            ".cyw",
            ".blf",
            ".osa",
            ".shs",
            ".xlm",
            ".exe_renamed",
            ".exe1",
            ".pif",
            ".xir",
            ".vbs",
            ".qrn",
            ".mjg",
            ".fag",
            ".xdu",
            ".xlam",
            ".com",
            ".ps2xml",
            ".reg",
            ".cpl",
            ".plc",
            ".ska",
            ".xlv",
            ".bmw",
            ".msc",
            ".tko",
            ".rna",
            ".msh2xml",
            ".wmf",
            ".hlw",
            ".uzy",
            ".nls",
            ".inf",
            ".iva",
            ".zix",
            ".gzquar",
            ".cxq",
            ".ppam",
            ".bps",
            ".ppt",
            ".dxz",
            ".ezt",
            ".jse",
            ".xnxx",
            ".xls",
            ".aru",
            ".lok",
            ".hta",
            ".vba",
            ".xltm",
            ".atm",
            ".xtbl",
            ".txs",
            ".xlsm",
            ".mjz",
            ".mfu",
            ".wsf",
            ".cih",
            ".xnt",
            ".capxml",
            ".sfx",
            ".fjl",
            ".cmd",
            ".msh",
            ".aut",
            ".ws",
            ".tti",
            ".dlb",
            ".msh1",
            ".ozd",
            ".fuj",
            ".exe",
            ".class",
            ".386",
            ".qit",
            ".ps2",
            ".delf",
            ".cla",
            ".ps1xml",
            ".bkd",
            ".bin",
            ".dev",
            ".cc",
            ".sys",
            ".dx",
            ".vbx",
            ".bup",
            ".vxd",
            ".rsc_tmp",
            ".spam",
            ".tps",
            ".htm",
            ".wsh",
            ".bll",
            ".sop",
            ".wsc",
            ".bxz",
            ".jar",
            ".tsa",
            ".msi",
            ".pcx",
            ".vbe",
            ".smm",
            ".rhk",
            ".dli",
            ".application",
            ".let",
            ".pid",
            ".upa",
            ".msh1xml",
            ".ce0",
            ".psc2",
            ".msh2",
            ".lpaq5",
            ".ctbl",
            ".boo",
            ".buk",
            ".hts",
            ".sldm",
            ".bat",
            ".smtmp",
            ".dllx",
            ".ppsm",
            ".docm",
            ".bhx",
            ".scf",
            ".fnr",
            ".pptm",
            ".drv",
            ".doc",
            ".vzr",
            ".ssy",
            ".scr",
            ".dotm",
            ".s7p",
            ".ceo",
            ".tmp",
            ".lik",
            ".lnk",
            ".pgm",
            ".dll",
            ".oar",
            ".bqf",
            ".zvz",
            ".dbd",
            ".vexe",
            ".potm",
            ".\u202e",
        }

    async def setup(self):
        pass

    async def extract(self, site: WebsiteData, executor: Executor) -> tuple[StarCase, Explanation, set[str]]:
        def extract_extensions(raw_links: list[str]) -> set[str]:
            def suffix(link: str):
                return os.path.splitext(urlparse(link)[2])[-1]

            return {suffix(link) for link in raw_links} - {""}

        extensions = extract_extensions(raw_links=site.raw_links)
        malicious = {extension for extension in extensions if extension in self.malicious_extensions}

        if len(malicious) > 0:
            return StarCase.ZERO, FOUND_POTENTIALLY_MALICIOUS_EXTENSION, malicious

        dangerous = {extension for extension in extensions if extension in self.dangerous_extensions}

        if len(dangerous) > 0:
            return StarCase.FOUR, FOUND_SLIGHTLY_MALICIOUS_EXTENSION, dangerous

        return StarCase.FIVE, NO_DANGEROUS_EXTENSIONS_FOUND, set()

from app.models import Explanation, StarCase
from core.metadata_base import MetadataBase
from core.website_manager import WebsiteData
from lib.constants import VALUES


class MaliciousExtensions(MetadataBase):
    # Based on: https://www.file-extensions.org/filetype/extension/name/dangerous-malicious-files
    #           https://www.howtogeek.com/137270/50-file-extensions-that-are-potentially-dangerous-on-windows/
    #           https://sensorstechforum.com/file-types-used-malware-2019/
    #           https://www.howtogeek.com/127154/how-hackers-can-disguise-malicious-programs-with-fake-file-extensions/
    more_harmless_extensions = ["docx", ".js", "pptx", ".html", "pdf"]
    malicious_extensions = [
        "msp",
        "cfxxe",
        "php3",
        "vb",
        "swf",
        "mcq",
        "dyv",
        "ps1",
        "9",
        "ocx",
        "chm",
        "mshxml",
        "lkh",
        "hlp",
        "iws",
        "gadget",
        "pr",
        "wlpginstall",
        "kcd",
        "dom",
        "hsq",
        "aepl",
        "0_full_0_tgod_signed",
        "dyz",
        "psc1",
        "py",
        "cyw",
        "blf",
        "osa",
        "shs",
        "xlm",
        "exe_renamed",
        "exe1",
        "pif",
        "xir",
        "vbs",
        "qrn",
        "mjg",
        "fag",
        "xdu",
        "xlam",
        "com",
        "ps2xml",
        "reg",
        "cpl",
        "plc",
        "ska",
        "xlv",
        "bmw",
        "msc",
        "tko",
        "rna",
        "msh2xml",
        "wmf",
        "hlw",
        "uzy",
        "nls",
        "inf",
        "iva",
        "zix",
        "gzquar",
        "cxq",
        "ppam",
        "bps",
        "ppt",
        "dxz",
        "ezt",
        "jse",
        "xnxx",
        "xls",
        "aru",
        "lok",
        "hta",
        "vba",
        "xltm",
        "atm",
        "xtbl",
        "txs",
        "xlsm",
        "mjz",
        "mfu",
        "wsf",
        "cih",
        "xnt",
        "capxml",
        "sfx",
        "fjl",
        "cmd",
        "msh",
        "aut",
        "ws",
        "tti",
        "dlb",
        "msh1",
        "ozd",
        "fuj",
        "exe",
        "class",
        "386",
        "qit",
        "ps2",
        "delf",
        "cla",
        "ps1xml",
        "bkd",
        "bin",
        "dev",
        "cc",
        "sys",
        "dx",
        "vbx",
        "bup",
        "vxd",
        "rsc_tmp",
        "spam",
        "tps",
        "htm",
        "wsh",
        "bll",
        "sop",
        "wsc",
        "bxz",
        "jar",
        "tsa",
        "msi",
        "pcx",
        "vbe",
        "smm",
        "rhk",
        "dli",
        "application",
        "let",
        "pid",
        "upa",
        "msh1xml",
        "ce0",
        "psc2",
        "msh2",
        "lpaq5",
        "ctbl",
        "boo",
        "buk",
        "hts",
        "sldm",
        "bat",
        "smtmp",
        "dllx",
        "ppsm",
        "docm",
        "bhx",
        "scf",
        "fnr",
        "pptm",
        "drv",
        "doc",
        "vzr",
        "ssy",
        "scr",
        "dotm",
        "s7p",
        "ceo",
        "tmp",
        "lik",
        "lnk",
        "pgm",
        "dll",
        "oar",
        "bqf",
        "zvz",
        "dbd",
        "vexe",
        "potm",
        "\u202e",
    ]
    decision_threshold = 0

    def _start(self, website_data: WebsiteData) -> dict:
        malicious_extensions = [
            extension
            for extension in website_data.extensions
            if extension.replace(".", "")
            in set(self.malicious_extensions + self.more_harmless_extensions)
        ]
        return {VALUES: malicious_extensions}

    def _decide(
        self, website_data: WebsiteData
    ) -> tuple[StarCase, list[Explanation]]:
        decision = StarCase.ZERO
        explanation = Explanation.none
        if len(website_data.values) == 0:
            decision = StarCase.FIVE
        else:
            for value in website_data.values:
                if value.replace(".", "") in self.malicious_extensions:
                    decision = StarCase.ZERO
                    explanation = (
                        Explanation.PotentiallyMaliciousExtensionFound
                    )
                    break
                elif value.replace(".", "") in self.more_harmless_extensions:
                    decision = StarCase.FOUR
                    explanation = Explanation.SlightlyMaliciousExtensionFound
        return decision, [explanation]

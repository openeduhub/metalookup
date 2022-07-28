from concurrent.futures import Executor

from metalookup.app.models import Explanation, StarCase
from metalookup.core.content import Content
from metalookup.core.extractor import Extractor

_FOUND_NON_EMBEDDED_JAVASCRIPT = "Found non embedded javascript block(s)"
_FOUND_NO_NON_EMBEDDED_JAVASCRIPT = "Found no non embedded javascript block(s)"


class Javascript(Extractor[set[str]]):
    """
    The returned extra data holds all src attributes, i.e. the locations from where scripts are loaded.
    """

    key = "javascript"

    async def setup(self):
        pass

    async def extract(self, content: Content, executor: Executor) -> tuple[StarCase, Explanation, set[str]]:
        matches = set()
        for script in (await content.soup()).select("script"):
            # fixme: as stated in the documentation (acceptance.md) we only consider script blocks with a
            #        `src` attribute as "javascript". However, the script could also be embedded (instead of loaded from
            #        somewhere). E.g.:
            #           <body>
            #           <p id="demo">Hi.</p>
            #           <script>
            #           document.getElementById("demo").innerHTML = "Hello World!";
            #           </script>
            #           </body>
            attributes = script.attrs
            if "src" in attributes.keys():
                matches.add(attributes["src"])

        found_matches = len(matches) > 0
        explanation = _FOUND_NON_EMBEDDED_JAVASCRIPT if found_matches else _FOUND_NO_NON_EMBEDDED_JAVASCRIPT
        star_case = StarCase.ZERO if found_matches else StarCase.FIVE
        return star_case, explanation, matches

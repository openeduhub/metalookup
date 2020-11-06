import json
import os
import subprocess
import time
from json import JSONDecodeError
from pathlib import Path

import pytest
import requests

DOCKER_TEST_URL = "http://0.0.0.0:5057/"
DOCKER_TEST_HEADERS = {"Content-Type": "application/json"}


def _build_and_run_docker():
    # Change to main project folder to have dockerfile etc. in scope
    current_dir = Path(os.getcwd())
    new_dir = current_dir.parents[0]
    if "tests" in str(current_dir):
        print(
            f"Changing working directory from '{current_dir}' to '{new_dir}'"
        )
        os.chdir(new_dir)

    print("Exporting requirements")
    process = subprocess.call(
        ["poetry export -o requirements.txt"], shell=True
    )
    print(f"process after exporting requirements: {process}")

    print("building docker")
    process = subprocess.call(
        ["docker build -t oeh-search-meta:latest ."], shell=True
    )

    print(f"process after building docker: {process}")

    # stopping any old container of the same name prior to launch

    subprocess.call(
        [
            "docker stop $(docker ps -a -q --filter ancestor=oeh-search-meta:latest --format='{{.ID}}')"
        ],
        shell=True,
    )

    process = subprocess.Popen(
        ["docker-compose -f docker-compose.yml up"], shell=True
    )
    print(f"process after docker-compose: {process}")

    # time needed for docker to launch and start the REST interface
    time.sleep(0.5)

    os.chdir(current_dir)


def _stop_docker():
    process = subprocess.call(
        [
            "docker stop $(docker ps -a -q --filter ancestor=oeh-search-meta:latest --format='{{.ID}}')"
        ],
        shell=True,
    )

    print(f"process after docker stop: {process}")


@pytest.mark.skip(
    reason="This test takes a lot of time, depending on payload etc. Execute manually."
)
def test_api_extract_meta():
    url = DOCKER_TEST_URL + "extract_meta"

    payload = (
        '{"url": "here", "content": '
        '{"html": "<OAI-PMH xmlns=\\"http://www.openarchives.org/OAI/2.0/\\" '
        'xmlns:xsi=\\"http://www.w3.org/2001/XMLSchema-instance\\" '
        'xsi:schemaLocation=\\"http://www.openarchives.org/OAI/2.0/ '
        'http://www.openarchives.org/OAI/2.0/OAI-PMH.xsd\\">'
        '<responseDate>2020-10-23T13:58:02Z</responseDate><request verb=\\"GetRecord\\" '
        'identifier=\\"4757e9ca-8829-4377-b0dd-680f1b2b4595\\" metadataPrefix=\\"lom\\">'
        "https://cloud.schulcampus-rlp.de/edu-sharing</request><GetRecord><record><header>"
        "<identifier>4757e9ca-8829-4377-b0dd-680f1b2b4595</identifier><datestamp>2020-10-23T13:58:02Z"
        '</datestamp></header><metadata><lom xmlns=\\"http://ltsc.ieee.org/xsd/LOM\\" xmlns:xsi=\\'
        '"http://www.w3.org/2001/XMLSchema-instance\\" xsi:schemaLocation=\\"http://ltsc.ieee.org/xsd/LOM  '
        'http://ltsc.ieee.org/xsd/lomv1.0/lom.xsd\\">\\n    <general>\\n        <identifier>\\n            '
        "<catalog>local</catalog>\\n            <entry>4757e9ca-8829-4377-b0dd-680f1b2b4595</entry>\\n        "
        '</identifier>\\n        <title>\\n            <string xmlns=\\"\\" language=\\"de\\">Triminos | '
        "paul-matthies.de - Tool um sie selber zu erstellen</string>\\n        </title>\\n        "
        '<description>\\n            <string xmlns=\\"\\" language=\\"de\\">Trimino-Generator</string>\\n'
        "        </description>\\n        <keyword>\\n            <string>Trimino</string>\\n        "
        "    <string>Domino</string>\\n            <string>kostenlos</string>\\n     "
        "       <string>Download</string>\\n            <string>Spiel</string>\\n         "
        '   <string>Schule</string>\\n            <string xmlns=\\"\\" language=\\"de\\">Quiz</string>\\n   '
        "     </keyword>\\n        <structure/>\\n        <aggregationLevel/>\\n    </general>\\n    "
        "<lifeCycle>\\n        <version>1.0</version>\\n        <status/>\\n        <contribute>\\n      "
        "      <role>\\n                <value>Author</value>\\n            </role>\\n            "
        "<entity>BEGIN:VCARD\\nFN: \\nN:;\\nVERSION:3.0\\nEND:VCARD</entity>\\n        </contribute>\\n    "
        "</lifeCycle>\\n    <metaMetadata>\\n        <contribute>\\n            <role>\\n                "
        "<value>creator</value>\\n            </role>\\n            <entity>"
        "BEGIN:VCARD\\nVERSION:3.0\\nN:Lachner;Birgit\\nFN:Birgit Lachner\\nORG:\\nURL:\\nTITLE:\\nTEL;"
        "TYPE=WORK,VOICE:\\nADR;TYPE=intl,postal,parcel,work:;;;;;;\\nEMAIL;TYPE=PREF,INTERNET:\\nEND:VCARD"
        "</entity>\\n        </contribute>\\n    </metaMetadata>\\n    <technical>\\n        <format>"
        "text/html</format>\\n        "
        "<location>https://cloud.schulcampus-rlp.de/edu-sharing/components/render/"
        "4757e9ca-8829-4377-b0dd-680f1b2b4595</location>\\n    </technical>\\n    <educational>\\n        "
        "<learningResourceType/>\\n        <intendedEndUserRole/>\\n    </educational>\\n    <rights>\\n  "
        "      <copyrightAndOtherRestrictions>\\n            <value>yes</value>\\n        "
        "</copyrightAndOtherRestrictions>\\n        <description>\\n            "
        '<string xmlns=\\"\\" language=\\"de\\">https://creativecommons.org/licenses/by-nc-sa/4.0</string>\\n'
        "        </description>\\n        <cost>no</cost>\\n    </rights>\\n    <relation>\\n        "
        "<kind>\\n            <source>LOM-DEv1.0</source>\\n            <value>hasthumbnail</value>\\n"
        "        </kind>\\n        <resource>\\n            <description>\\n                "
        '<string xmlns=\\"\\" language=\\"en\\">'
        "https://cloud.schulcampus-rlp.de/edu-sharing/preview?nodeId=4757e9ca-8829-4377-b0dd-680f1b2b4595&amp;"
        "storeProtocol=workspace&amp;storeId=SpacesStore&amp;dontcache=1603461482271</string>\\n            "
        "</description>\\n        </resource>\\n    </relation>\\n</lom></metadata></record></GetRecord>"
        "</OAI-PMH>\", \"headers\":\"{b'Date': [b'Fri, 23 Oct 2020 13:58:01 GMT'], b'Server': [b'Apache'], "
        "b'Access-Control-Expose-Headers': [b'X-Edu-Scope'], b'Cache-Control': [b'no-cache'], "
        "b'Expires': [b'0'], b'Content-Type': [b'application/xml'], b'Vary': [b'Accept-Encoding'],"
        " b'X-Content-Type-Options': [b'nosniff'], b'X-Frame-Options': [b'sameorigin']}\"}}"
    )

    _build_and_run_docker()

    response = requests.request(
        "POST", url, headers=DOCKER_TEST_HEADERS, data=payload, timeout=60
    )

    try:
        data = json.loads(response.text)
        is_json = True
    except JSONDecodeError:
        data = {}
        is_json = False
    has_url = "url" in data.keys()
    has_meta = "url" in data.keys()

    assert is_json and has_url and has_meta


def test_ping_container():
    url = DOCKER_TEST_URL + "_ping"

    _build_and_run_docker()

    response = requests.request(
        "GET", url, headers=DOCKER_TEST_HEADERS, timeout=60
    )

    data = json.loads(response.text)
    is_ok = data["status"] == "ok"
    assert is_ok

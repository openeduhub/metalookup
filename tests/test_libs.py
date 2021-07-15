import os
import subprocess
import time
from pathlib import Path

DOCKER_TEST_URL = "http://127.0.0.1:5057/"
DOCKER_TEST_HEADERS = {"Content-Type": "application/json"}


def _build_and_run_docker():
    # Change to main project folder to have dockerfile etc. in scope
    current_dir = Path(os.getcwd())
    if "tests" in str(current_dir):
        new_dir = current_dir.parents[0]
        while "tests" in str(new_dir):
            new_dir = new_dir.parent
        print(
            f"Changing working directory from '{current_dir}' to '{new_dir}'"
        )
        os.chdir(new_dir)

    print("Exporting requirements")
    process = subprocess.call(
        ["poetry export -o requirements.txt"], shell=True
    )
    print(f"process after exporting requirements: {process}")

    # stopping any old container of the same name prior to launch

    subprocess.call(
        [
            "docker stop $(docker ps -a -q --filter ancestor=community.docker.edu-sharing.com/oeh-search-meta:latest --format='{{.ID}}')"
        ],
        shell=True,
    )
    subprocess.call(
        [
            "docker stop $(docker ps -a -q --filter ancestor=community.docker.edu-sharing.com/oeh-search-meta_lighthouse:latest --format='{{.ID}}')"
        ],
        shell=True,
    )

    print("building docker")
    process = subprocess.call(
        [
            "docker build -t community.docker.edu-sharing.com/oeh-search-meta:latest ."
        ],
        shell=True,
    )

    print(f"process after building docker: {process}")

    print("building lighthouse docker")
    process = subprocess.call(
        [
            "docker build -f dockerfile_lighthouse -t community.docker.edu-sharing.com/oeh-search-meta_lighthouse:latest ."
        ],
        shell=True,
    )

    print(f"process after building lighthouse docker: {process}")

    process = subprocess.Popen(
        ["docker-compose -f docker-compose.yml up"], shell=True
    )
    print(f"process after docker-compose: {process}")

    # time needed for docker to launch and start the REST interface
    # time_for_meta + time_for_lighthouse + time_for_running_parallel_tests
    maximum_wait_time = 10
    start = time.perf_counter()
    while time.perf_counter() - start < maximum_wait_time:
        try:
            subprocess.check_output(
                "docker ps | grep 'oeh-search-meta_extractor_1'", shell=True
            )
        except subprocess.CalledProcessError:
            print(
                f"Waited {time.perf_counter() - start}s for containers to launch."
            )
            time.sleep(0.1)

    os.chdir(current_dir)

import random
from pathlib import Path

from locust import HttpUser, between, task


def load_urls():
    with open(Path(__file__).parent.parent / "resources" / "urls.txt", "r") as f:
        urls = f.readlines()
        print(f"Loaded {len(urls)}. sample: {urls[0:10]}")
        return urls


class ExtractUser(HttpUser):
    wait_time = between(1, 5)
    urls = load_urls()

    @task
    def hello_world(self):
        self.client.post("/extract", json={"url": random.choice(self.urls)})

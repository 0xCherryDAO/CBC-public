import random
from typing import Any

from src.utils.data.helper import proxies


class Proxy:
    def __init__(self, proxy_url: str, change_link: str | None = None):
        self.change_link = change_link
        self.proxy_url = proxy_url
        self._client = None

    def attach_client(self, client: Any):
        self._client = client

    def _get_random_proxy(self) -> str:
        proxy_str = random.choice(proxies)
        return f"http://{proxy_str}"

    async def change(self):
        self.proxy_url = self._get_random_proxy()
        if self._client:
            self._client.reinitialize_proxy_clients()

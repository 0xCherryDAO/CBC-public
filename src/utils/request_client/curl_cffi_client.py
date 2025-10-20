import platform
from typing import Dict, Any

from curl_cffi.requests import AsyncSession, BrowserType

from src.utils.proxy_manager import Proxy


class CurlCffiClient:
    def __init__(self, proxy: Proxy | None):
        self.session = AsyncSession(
            proxies={
                'http': proxy.proxy_url if proxy else None,
                'https': proxy.proxy_url if proxy else None
            },
            impersonate=BrowserType.chrome131 if platform.system() == 'Windows' else BrowserType.chrome131
        )

    async def make_request(
            self,
            method: str = 'GET',
            url: str = None,
            headers: Dict[str, Any] = None,
            data: str = None,
            json: Dict[str, Any] = None,
            params: Dict[str, Any] = None,
            cookies: Dict[str, Any] = None,
            return_text: bool = False,
            return_full_response: bool = False
    ):
        response = await self.session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=headers,
            json=json,
            cookies=cookies,
            verify=False
        )
        status = response.status_code

        if return_full_response:
            full_resp = response
            await response.aclose()
            return full_resp

        if response.status_code in [200, 201]:
            if return_text:
                text_resp = response.text
                await response.aclose()
                return text_resp, status
            json_resp = response.json()
            await response.aclose()
            return json_resp, status
        else:
            text_resp = response.text
            await response.aclose()
            return text_resp, status

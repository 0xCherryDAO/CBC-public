from functools import wraps
from asyncio import sleep

from typing import Callable

from loguru import logger


def retry(retries: int, delay: int, backoff: float) -> Callable:
    def decorator_retry(func: Callable) -> Callable:
        @wraps(func)
        async def wrapped(self, *args, **kwargs):
            for attempt in range(retries + 1):
                try:
                    return await func(self, *args, **kwargs)
                except Exception as ex:
                    if attempt == retries:
                        logger.error(f'{func.__name__} failed after {retries} retries: {ex}')
                        return None
                    if 'host' in str(ex).lower() or 'proxy' in str(ex).lower() or 'http' in str(ex).lower():
                        if hasattr(self, 'proxy') and hasattr(self.proxy, 'change'):
                            logger.warning(f'[{func.__name__}] Attempt {attempt + 1} failed. Changing proxy...')
                            await self.proxy.change()
                    await sleep(delay * (backoff ** attempt))
        return wrapped
    return decorator_retry

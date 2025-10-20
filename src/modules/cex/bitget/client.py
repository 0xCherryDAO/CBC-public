from typing import Optional, Callable

from loguru import logger

from src.models.cex import CEXConfig
from src.utils.proxy_manager import Proxy
from src.utils.abc.abc_cex import CEX


class Bitget(CEX):
    def __init__(
            self,
            config: CEXConfig,
            private_key: str,
            proxy: Proxy | None
    ):
        super().__init__(private_key=private_key, proxy=proxy, config=config)

    def __str__(self) -> str:
        if self.config.bitget_config.withdraw_settings:
            return (
                f'[{self.wallet_address}] | [{self.__class__.__name__}] | Withdrawing {self.amount} {self.token} '
                f'to {self.to_address} | CHAIN: {self.chain}')
        else:
            return (f'[{self.wallet_address}] | [{self.__class__.__name__}] | Depositing {self.token}'
                    f' to {self.to_address} | CHAIN: {self.chain}')

    def call_withdraw(self, exchange_instance) -> Optional[bool]:
        try:
            self.amount = round(self.amount, 4)
            self.exchange_instance.withdraw(
                code=self.token.upper(),
                amount=self.amount,
                address=self.to_address.lower(),
                tag=None,
                params={
                    'network': self.chain.upper()
                }
            )
            logger.success(
                f'Successfully withdrawn {self.amount} {self.token} to {self.chain} for wallet {self.to_address}')
            return True

        except Exception as ex:
            logger.error(f'Something went wrong {ex}')
            return None

    async def call_sub_transfer(
            self, token: str, api_key: str, api_secret: str, api_passphrase: Optional[str],
            api_password: Optional[str], request_func: Callable
    ) -> None:
        pass

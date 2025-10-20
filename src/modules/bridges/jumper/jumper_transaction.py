from typing import Optional, Callable, Any, Dict

from eth_typing import ChecksumAddress
from web3.contract import AsyncContract
from web3.types import TxParams

from src.models.bridge import BridgeConfig


async def get_transaction_data(self, steps: list, headers: dict) -> Optional[dict]:
    response_json, status = await self.make_request(
        method="POST",
        url='https://api.jumper.exchange/p/lifi/advanced/stepTransaction',
        headers=headers,
        json=steps[0]
    )
    if status == 200:
        return response_json['transactionRequest']


async def create_jumper_tx(
        self,
        contract: Optional[AsyncContract],
        bridge_config: BridgeConfig,
        amount: int
) -> Optional[tuple[TxParams | Dict | None, Optional[str]]]:
    headers = {
        'accept': '*/*',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://jumper.exchange',
        'priority': 'u=1, i',
        'referer': 'https://jumper.exchange/',
        'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'x-lifi-integrator': 'jumper.exchange',
        'x-lifi-sdk': '3.12.11',
        'x-lifi-widget': '3.32.2',
    }

    steps = await get_steps(
        self,
        bridge_config.from_token.name,
        bridge_config.to_token.name,
        bridge_config.from_token.address,
        bridge_config.to_token.address,
        amount,
        self.wallet_address,
        self.make_request,
        bridge_config.to_chain.chain_id,
        bridge_config,
        headers
    )
    if not steps:
        return None, None

    transaction_data = await get_transaction_data(self, steps, headers)

    tx = {
        'from': self.wallet_address,
        'value': int(transaction_data['value'], 16),
        'to': self.web3.to_checksum_address(transaction_data['to']),
        'nonce': await self.web3.eth.get_transaction_count(self.wallet_address),
        'chainId': await self.web3.eth.chain_id,
        'gasPrice': int(await self.web3.eth.gas_price * 1.15),
        'data': transaction_data['data']
    }
    return tx, transaction_data['to']


async def get_steps(
        self, from_token: str, to_token: str, from_token_address: str, to_token_address: str,
        amount: int, wallet_address: ChecksumAddress, request_function: Callable, destination_chain_id: int,
        bridge_config: BridgeConfig, headers: dict
) -> list[Any]:
    json_data = {
        'fromAddress': wallet_address,
        'fromAmount': str(amount),
        'fromChainId': await self.web3.eth.chain_id,
        'fromTokenAddress': '0x0000000000000000000000000000000000000000' if
        from_token.upper() == bridge_config.from_chain.native_token.upper() else from_token_address,
        'toChainId': destination_chain_id,
        'toTokenAddress': '0x0000000000000000000000000000000000000000' if
        to_token.upper() == bridge_config.to_chain.native_token.upper() else to_token_address,
        'options': {
            'integrator': 'jumper.exchange',
            'order': 'CHEAPEST',
            'maxPriceImpact': 0.4,
            'allowSwitchChain': True,
        },
    }

    response_json, status = await self.make_request(
        method='POST',
        url='https://api.jumper.exchange/p/lifi/advanced/routes',
        headers=headers,
        json=json_data
    )
    return response_json['routes'][0]['steps']

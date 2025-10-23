import random

from asyncio import sleep
from typing import Optional, Any, Type

from loguru import logger

from src.models.bridge import BridgeConfig
from src.models.cex import OKXConfig, CEXConfig, BinanceConfig, BitgetConfig, DepositSettings
from src.models.chain import Chain
from src.models.route import Route
from src.models.token import Token
from src.modules.bridges.bridge_factory import RelayBridge, JumperBridge
from src.modules.cex.binance.client import Binance
from src.modules.cex.bitget.client import Bitget
from src.modules.cex.okx.client import OKX
from src.utils.data.chains import chain_mapping
from src.utils.data.tokens import tokens
from src.utils.proxy_manager import Proxy
from src.utils.user.account import Account
from src.models.cex import WithdrawSettings
from config import *


async def process_cex_withdraw(route: Route) -> Optional[bool]:
    if await _already_has_enough_balance_generic(route, CEXWithdrawSettings):
        return True
    account = Account(
        private_key=route.wallet.private_key,
        proxy=route.wallet.proxy
    )
    token = CEXWithdrawSettings.to_token

    chain = CEXWithdrawSettings.to_chain
    amount = CEXWithdrawSettings.amount

    withdraw_settings = WithdrawSettings(
        token=token,
        chain=chain,
        to_address=str(account.wallet_address),
        amount=amount
    )

    cex = CEXWithdrawSettings.cex.lower().capitalize()

    if cex == 'Binance':
        cex_object = Binance
        binance_config = BinanceConfig(
            deposit_settings=None,
            withdraw_settings=withdraw_settings,
            API_KEY=BinanceSettings.BINANCE_KEY,
            API_SECRET=BinanceSettings.BINANCE_SECRET,
            PROXY=BinanceSettings.PROXY
        )
        okx_config = None
        bitget_config = None

    elif cex == 'Okx':
        cex_object = OKX
        okx_config = OKXConfig(
            deposit_settings=None,
            withdraw_settings=withdraw_settings,
            API_KEY=OKXSettings.API_KEY,
            API_SECRET=OKXSettings.API_SECRET,
            PASSPHRASE=OKXSettings.API_PASSWORD,
            PROXY=OKXSettings.PROXY
        )
        binance_config = None
        bitget_config = None
    elif cex == 'Bitget':
        cex_object = Bitget
        bitget_config = BitgetConfig(
            deposit_settings=None,
            withdraw_settings=withdraw_settings,
            API_KEY=BitgetSettings.BITGET_KEY,
            API_SECRET=BitgetSettings.BITGET_SECRET,
            PASSWORD=BitgetSettings.BITGET_PASSWORD,
            PROXY=BitgetSettings.PROXY
        )
        okx_config = None
        binance_config = None
    else:
        raise ValueError(f'cex must be one of these: Binance/OKX/Bitget. Got {cex}')

    config = CEXConfig(
        okx_config=okx_config,
        binance_config=binance_config,
        bitget_config=bitget_config,
    )
    cex = cex_object(
        config=config,
        private_key=route.wallet.private_key,
        proxy=OKXSettings.PROXY
    )

    logger.debug(cex)
    return await cex.withdraw()


async def get_balances_for_chains(
        chains: list[str],
        private_key: str,
        proxy: Proxy | None = None
) -> Optional[dict[str, int]]:
    balances = {}

    for chain_name in chains:
        rpc = chain_mapping[chain_name].rpc

        while True:
            account = Account(private_key=private_key, rpc=rpc, proxy=proxy)
            wallet_address = account.wallet_address
            try:
                balance = await account.web3.eth.get_balance(wallet_address)
                break
            except Exception as ex:
                logger.info(f'Не удалось проверить баланс | {ex}')
                if 'proxy' in str(ex).lower() or 'http' in str(ex).lower() or 'host' in str(ex):
                    logger.debug('Changing proxy...')
                    await proxy.change()
                await sleep(2)
        balances[chain_name] = balance

    return balances


def _as_list(x: Any) -> list:
    if x is None:
        return []
    if isinstance(x, (list, tuple, set)):
        return list(x)
    return [x]


async def _already_has_enough_balance_generic(route: Route, settings: Any) -> Optional[bool]:
    tokens_min_balances = getattr(settings, "to_token_min_balances", {})
    chains = _as_list(getattr(settings, "to_chain"))
    allowed_to_tokens = set(_as_list(getattr(settings, "to_token")))

    for chain_symbol in chains:
        account = Account(
            private_key=route.wallet.private_key, proxy=None, rpc=chain_mapping[chain_symbol.upper()].rpc
        )

        chain_map = tokens_min_balances.get(chain_symbol, {})
        for exact_token, min_balance in chain_map.items():
            if allowed_to_tokens and exact_token not in allowed_to_tokens:
                continue

            chain_symbol = min(
                (k for k, v in chain_mapping.items() if v is chain_mapping[chain_symbol.upper()]),
                key=lambda k: (' ' in k, len(k), k)
            )

            is_native = exact_token == chain_mapping[chain_symbol.upper()].native_token
            token_address = tokens[chain_symbol.upper()][exact_token]

            try:
                balance = await account.get_wallet_balance(is_native=is_native, address=token_address)
                decimals = 18
                if not is_native:
                    decimals = await account.get_decimals(contract_address=token_address, web3=account.web3)

                if balance >= min_balance * 10 ** decimals:
                    logger.debug(
                        f"[{account.wallet_address}] | В токене {exact_token} уже есть достаточный баланс"
                        f" | {round(balance / 10 ** decimals, 3)} {exact_token}."
                    )
                    return True
            except Exception:
                return False


def _pick_to_chain(settings: Any) -> Optional[str]:
    to_chain = getattr(settings, "to_chain", None)
    if to_chain is None:
        return None
    if isinstance(to_chain, list):
        return random.choice(to_chain) if to_chain else None
    return to_chain


def _pick_amount(settings: Any) -> float:
    amt = getattr(settings, "amount", 0)
    if isinstance(amt, (list, tuple)) and len(amt) == 2:
        return float(random.uniform(amt[0], amt[1]))
    return float(amt)


def _build_bridge_config(from_chain: str, to_chain: str, from_token: Any, to_token: Any,
                         amount: float, use_percentage: bool, bridge_percentage: float) -> BridgeConfig:
    return BridgeConfig(
        from_chain=Chain(
            chain_name=from_chain,
            native_token=chain_mapping[from_chain.upper()].native_token,
            rpc=chain_mapping[from_chain.upper()].rpc,
            chain_id=chain_mapping[from_chain.upper()].chain_id,
        ),
        to_chain=Chain(
            chain_name=to_chain,
            native_token=chain_mapping[to_chain.upper()].native_token,
            rpc=chain_mapping[to_chain.upper()].rpc,
            chain_id=chain_mapping[to_chain.upper()].chain_id,
        ),
        from_token=Token(chain_name=from_chain, name=from_token),
        to_token=Token(chain_name=to_chain, name=to_token),
        amount=amount,
        use_percentage=use_percentage,
        bridge_percentage=bridge_percentage,
    )


async def _process_bridge(route: Route, settings: Any, BridgeCls: Type) -> Optional[bool]:
    if await _already_has_enough_balance_generic(route, settings):
        return True

    from_candidates = _as_list(getattr(settings, "from_chain", []))
    balances = await get_balances_for_chains(from_candidates, route.wallet.private_key, route.wallet.proxy)
    if not balances:
        return None
    from_chain = max(balances, key=balances.get)

    to_chain = _pick_to_chain(settings)
    amount = _pick_amount(settings)

    use_percentage = bool(getattr(settings, "use_percentage", False))
    bridge_percentage = getattr(settings, "bridge_percentage", 0)

    from_token = _as_list(getattr(settings, "from_token"))
    to_token = getattr(settings, "to_token")

    bridged = None
    for token in from_token:
        bridge = BridgeCls(
            private_key=route.wallet.private_key,
            proxy=route.wallet.proxy,
            bridge_config=_build_bridge_config(
                from_chain=from_chain,
                to_chain=to_chain,
                from_token=token,
                to_token=to_token,
                amount=amount,
                use_percentage=use_percentage,
                bridge_percentage=bridge_percentage,
            ),
        )
        logger.debug(bridge)
        bridged = await bridge.bridge()
        await sleep(5)

    return bridged


async def process_relay_bridge(route: Route) -> Optional[bool]:
    return await _process_bridge(route, RelayBridgeSettings, RelayBridge)


async def process_jumper_bridge(route: Route) -> Optional[bool]:
    return await _process_bridge(route, JumperBridgeSettings, JumperBridge)


async def process_cex_deposit(route: Route) -> bool:
    chains = CEXDepositSettings.chains
    token = CEXDepositSettings.token
    keep_balances = CEXDepositSettings.keep_balances

    random.shuffle(chains)

    successes = 0
    for chain in chains:
        okx_config = OKXConfig(
            deposit_settings=DepositSettings(
                token=token,
                chain=chain,
                to_address=route.wallet.recipient,
                keep_balance=keep_balances[chain.upper()]
            ),
            withdraw_settings=None,
            API_KEY=OKXSettings.API_KEY,
            API_SECRET=OKXSettings.API_SECRET,
            PASSPHRASE=OKXSettings.API_PASSWORD,
            PROXY=OKXSettings.PROXY
        )

        config = CEXConfig(
            okx_config=okx_config,
        )
        cex = OKX(
            config=config,
            private_key=route.wallet.private_key,
            proxy=OKXSettings.PROXY
        )

        transferred = await cex.deposit()
        if transferred:
            successes += 1

        random_sleep = random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1]) if isinstance(
            PAUSE_BETWEEN_MODULES, list) else PAUSE_BETWEEN_MODULES
        logger.info(f'Сплю {random_sleep} секунд перед следующим трансфером...')
        await sleep(random_sleep)

    return successes > 0

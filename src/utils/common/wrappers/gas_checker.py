import asyncio

from web3 import AsyncWeb3
from web3.eth import AsyncEth

from loguru import logger

from config import MAX_GWEI
from src.utils.data.chains import ETH


async def get_gas():
    try:
        w3 = AsyncWeb3(
            AsyncWeb3.AsyncHTTPProvider(ETH.rpc),
            modules={"eth": (AsyncEth,)},
        )
        gas_price = await w3.eth.gas_price
        gwei = w3.from_wei(gas_price, 'gwei')
        return gwei
    except Exception as error:
        logger.error(error)


async def wait_gas():
    while True:
        gas = await get_gas()

        if gas > MAX_GWEI:
            logger.warning(f'Current GWEI: {gas} > {MAX_GWEI}')
            await asyncio.sleep(60)
        else:
            logger.debug(f"GWEI is normal | current: {gas} < {MAX_GWEI}")
            break


def check_gas(func):
    async def _wrapper(*args, **kwargs):
        await wait_gas()
        return await func(*args, **kwargs)

    return _wrapper

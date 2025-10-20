from typing import Callable
from hashlib import sha256
from asyncio import sleep
from time import time
import hmac

from loguru import logger


def parse_params(params: dict | None = None) -> str:
    if params:
        sorted_keys = sorted(params)
        params_str = "&".join(["%s=%s" % (x, params[x]) for x in sorted_keys])
    else:
        params_str = ''
    return params_str + "&timestamp=" + str(int(time() * 1000))


def get_sign(payload: str = "", *, api_secret: str) -> str:
    try:
        secret_key_bytes = api_secret.encode('utf-8')
        signature = hmac.new(secret_key_bytes, payload.encode('utf-8'), sha256).hexdigest()

        return signature
    except Exception as ex:
        logger.error(ex)


async def get_sub_list(api_key: str, api_secret: str, make_request: Callable):
    path = "/sapi/v1/sub-account/list"

    params = parse_params()
    url = f"https://api.binance.com{path}?{params}&signature={get_sign(params, api_secret=api_secret)}"
    headers = {
        "Content-Type": "application/json",
        "X-MBX-APIKEY": api_key,
    }
    response_json = await make_request(
        method='GET',
        url=url,
        headers=headers
    )
    sub_list = response_json['subAccounts']
    return sub_list


async def get_sub_balance(sub_email, api_key: str, api_secret: str, make_request: Callable):
    path = '/sapi/v3/sub-account/assets'

    params = {
        "email": sub_email
    }

    params = parse_params(params)
    url = f"https://api.binance.com{path}?{params}&signature={get_sign(params, api_secret=api_secret)}"
    headers = {
        "Content-Type": "application/json",
        "X-MBX-APIKEY": api_key,
    }
    response_json = await make_request(
        method='GET',
        url=url,
        headers=headers,
    )
    return response_json


async def transfer_from_subaccs_to_main(
        api_key: str, api_secret: str, token: str, make_request: Callable
) -> None:
    sub_list = await get_sub_list(api_key, api_secret, make_request)

    for sub_data in sub_list:
        sub_email = sub_data['email']

        sub_balances = await get_sub_balance(sub_email, api_key, api_secret, make_request)
        asset_balances = [balance for balance in sub_balances['balances'] if balance['asset'] == token]
        sub_balance = 0 if len(asset_balances) == 0 else float(asset_balances[0]['free'])

        amount = sub_balance
        if sub_balance == amount and sub_balance != 0.0:
            logger.debug(f'{sub_email} | balance : {sub_balance} {token}')

            params = {
                "amount": amount,
                "asset": token,
                "fromAccountType": "SPOT",
                "toAccountType": "SPOT",
                "fromEmail": sub_email
            }

            path = "/sapi/v1/sub-account/universalTransfer"

            while True:
                try:
                    params = parse_params(params)
                    url = f"https://api.binance.com{path}?{params}&signature={get_sign(params, api_secret=api_secret)}"
                    headers = {
                        "Content-Type": "application/json",
                        "X-MBX-APIKEY": api_key,
                    }
                    response = await make_request(
                        method='POST',
                        url=url,
                        headers=headers
                    )
                    if 'assets have been frozen and are currently unable to be withdrawn' in str(response):
                        logger.warning(f'Блоки еще не подтвердились.')
                        break
                    logger.success(
                        f"Successfully transferred {amount} {token} to main account"
                    )
                    break
                except Exception as error:
                    if 'not reached the required block confirmations' in str(error) or '-9000' in str(error):
                        logger.warning(
                            "Deposit not reached the required block confirmations. Will try again in 1 min..."
                        )
                        await sleep(60)

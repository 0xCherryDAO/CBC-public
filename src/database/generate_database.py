from getpass import getpass
import random

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete

from loguru import logger
from eth_account import Account

from src.database.base_models.pydantic_manager import DataBaseManagerConfig
from src.database.models import WorkingWallets, WalletsTasks
from src.database.utils.db_manager import DataBaseUtils
from config import *
from src.utils.encryption import encrypt_data


async def clear_database(engine) -> None:
    async with AsyncSession(engine) as session:
        async with session.begin():
            for model in [WorkingWallets, WalletsTasks]:
                await session.execute(delete(model))
            await session.commit()
    logger.info("The database has been cleared")


async def generate_database(
        engine,
        private_keys: list[str],
        proxies: list[str],
        recipients: list[str]
) -> None:
    await clear_database(engine)
    tasks = []

    if CEX_WITHDRAW: tasks.append('CEX_WITHDRAW')
    if RELAY_BRIDGE: tasks.append('RELAY_BRIDGE')
    if CEX_DEPOSIT: tasks.append('CEX_DEPOSIT')
    if JUMPER_BRIDGE: tasks.append('JUMPER_BRIDGE')

    has_cex_withdraw = 'CEX_WITHDRAW' in tasks
    has_relay_bridge = 'RELAY_BRIDGE' in tasks
    has_jumper_bridge = 'JUMPER_BRIDGE' in tasks

    proxy_index = 0

    logger.info("🔐 Введите пароль для шифрования приватных ключей:")
    encryption_password = getpass(">>> ")

    for private_key in private_keys:
        address = Account.from_key(private_key).address

        salt, encrypted_key = encrypt_data(private_key, encryption_password)

        with open('data/wallets.txt', 'r') as file:
            file_private_keys = [line.strip() for line in file]

        other_tasks = [
            task for task in tasks if
            task not in ['CEX_WITHDRAW', 'RELAY_BRIDGE', 'JUMPER_BRIDGE']
        ]
        random.shuffle(other_tasks)
        tasks = (
                (['CEX_WITHDRAW'] if has_cex_withdraw else []) +
                (['RELAY_BRIDGE'] if has_relay_bridge else []) +
                (['JUMPER_BRIDGE'] if has_jumper_bridge else []) +
                other_tasks
        )

        private_key_index = file_private_keys.index(private_key)

        recipient_address = None
        if 'CEX_DEPOSIT' in tasks:
            if len(private_keys) != len(recipients):
                logger.error(f'Number of private keys does not match number of recipients')
                return

            recipient_address = recipients[private_key_index]

        if len(proxies) >= len(private_keys):
            proxy = proxies[private_key_index]
        else:
            proxy = proxies[proxy_index]
            proxy_index = (proxy_index + 1) % len(proxies)

        proxy_url = None

        if proxy:
            proxy_url = proxy

        db_utils = DataBaseUtils(
            manager_config=DataBaseManagerConfig(
                action='working_wallets'
            )
        )

        await db_utils.add_to_db(
            private_key=encrypted_key,
            address=address,
            salt=salt,
            proxy=proxy_url,
            recipient_address=recipient_address,
            status='pending',
        )

        for task in tasks:
            db_utils = DataBaseUtils(
                manager_config=DataBaseManagerConfig(
                    action='wallets_tasks'
                )
            )
            await db_utils.add_to_db(
                private_key=encrypted_key,
                address=address,
                status='pending',
                task_name=task
            )

from getpass import getpass
from typing import List, Optional

from loguru import logger

from src.database.base_models.pydantic_manager import DataBaseManagerConfig
from src.database.utils.db_manager import DataBaseUtils
from src.models.route import Route, Wallet
from src.utils.encryption import decrypt_data


async def get_routes() -> Optional[List[Route]]:
    db_utils = DataBaseUtils(
        manager_config=DataBaseManagerConfig(
            action='working_wallets'
        )
    )
    result = await db_utils.get_uncompleted_wallets()
    if not result:
        logger.success(f'Все кошельки с данной базы данных уже отработали')
        return None

    routes = []
    logger.info("🔐 Введите пароль для расшифровки приватных ключей:")
    decryption_password = getpass(">>> ")

    for wallet in result:
        private_key_tasks = await db_utils.get_wallet_pending_tasks(wallet.private_key)
        tasks = []
        for task in private_key_tasks:
            tasks.append(task.task_name)

        private_key = decrypt_data(wallet.private_key, decryption_password, wallet.salt)
        routes.append(
            Route(
                tasks=tasks,
                wallet=Wallet(
                    encrypted_key=wallet.private_key,
                    private_key=private_key,
                    address=wallet.address,
                    proxy=wallet.proxy,
                    recipient=wallet.recipient
                )
            )
        )
    return routes

from asyncio import run, set_event_loop_policy, gather, create_task, sleep, Lock
from typing import Awaitable, Callable
import os, platform

import random
import asyncio
import logging
import sys

from rich.console import Console
from src.utils.version import print_logo
from questionary import select, Choice
from loguru import logger

from config import *
from src.utils.data.helper import private_keys, proxies, recipients
from src.database.generate_database import generate_database
from src.database.models import init_models, engine
from src.utils.data.mappings import module_handlers
from src.utils.manage_tasks import manage_tasks
from src.utils.retrieve_route import get_routes
from src.models.route import Route
from src.utils.tg_app.telegram_notifications import TGApp

logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.CRITICAL)

if sys.platform == 'win32':
    set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

processed_wallets_counter = 0
processed_wallets_lock = Lock()


def get_module():
    result = select(
        message="Choose module",
        choices=[
            Choice(title="1) Generate new database", value=1),
            Choice(title="2) Work with existing database", value=2)
        ],
        qmark="⚙️ ",
        pointer="🍒 "
    ).ask()
    return result


async def process_task(routes: list[Route]) -> None:
    if not routes:
        logger.success(f'All tasks are completed')
        return

    semaphore = asyncio.Semaphore(MAX_PARALLEL_ACCOUNTS)

    async def process_route_with_semaphore(route: Route) -> None:
        async with semaphore:
            await process_route(route)

    wallet_tasks = []
    for i, route in enumerate(routes):
        wallet_tasks.append(create_task(process_route_with_semaphore(route)))

        if i < len(routes) - 1:
            time_to_pause = random.randint(PAUSE_BETWEEN_WALLETS[0], PAUSE_BETWEEN_WALLETS[1]) \
                if isinstance(PAUSE_BETWEEN_WALLETS, list) else PAUSE_BETWEEN_WALLETS
            logger.info(f'Сплю {time_to_pause} секунд перед следующим кошельком...')
            await sleep(time_to_pause)

    await gather(*wallet_tasks)


async def process_route(route: Route) -> None:
    private_key = route.wallet.private_key

    for task in route.tasks:
        completed = await module_handlers[task](route)

        if completed:
            await manage_tasks(route.wallet.encrypted_key, route.wallet.address, task)

        time_to_pause = random.randint(PAUSE_BETWEEN_MODULES[0], PAUSE_BETWEEN_MODULES[1]) \
            if isinstance(PAUSE_BETWEEN_MODULES, list) else PAUSE_BETWEEN_MODULES

        logger.info(f'Sleeping {time_to_pause} seconds before next module...')
        await sleep(time_to_pause)

    if TG_BOT_TOKEN and TG_USER_ID:
        global processed_wallets_counter
        global processed_wallets_lock

        async with processed_wallets_lock:
            processed_wallets_counter += 1
            current_index = processed_wallets_counter

        tg_app = TGApp(
            token=TG_BOT_TOKEN,
            tg_id=TG_USER_ID,
            private_key=private_key,
            encrypted_key=route.wallet.encrypted_key,
            processed_index=current_index,
        )
        await tg_app.send_message()


async def main(module: Callable) -> None:
    await init_models(engine)
    if module == 1:
        if SHUFFLE_WALLETS:
            random.shuffle(private_keys)
        logger.debug("Generating new database")
        await generate_database(engine, private_keys, proxies, recipients)
    elif module == 2:
        logger.debug("Working with the database")
        routes = await get_routes()
        await process_task(routes)
    else:
        print("Wrong choice")
        return


def start_event_loop(awaitable: Awaitable[None]) -> None:
    run(awaitable)


if __name__ == '__main__':
    console = Console()
    print_logo(console)
    module = get_module()
    start_event_loop(main(module))

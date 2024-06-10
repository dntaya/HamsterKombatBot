import os
import glob
import asyncio
import argparse
from itertools import cycle

from bot.utils.client import Client
from better_proxy import Proxy

from bot.config import settings
from bot.utils import logger
from bot.core.tapper import run_tapper
from bot.core.registrator import register_client, register_client_by_tg_auth, migrate_old_clients


start_text = """

▒█ ▒█ █▀▀█ █▀▄▀█ █▀▀ ▀▀█▀▀ █▀▀ █▀▀█ ▒█ ▄▀ █▀▀█ █▀▄▀█ █▀▀▄ █▀▀█ ▀▀█▀▀ ▒█▀▀█ █▀▀█ ▀▀█▀▀ 
▒█▀▀█ █▄▄█ █ ▀ █ ▀▀█   █   █▀▀ █▄▄▀ ▒█▀▄  █  █ █ ▀ █ █▀▀▄ █▄▄█   █   ▒█▀▀▄ █  █   █   
▒█ ▒█ ▀  ▀ ▀   ▀ ▀▀▀   ▀   ▀▀▀ ▀ ▀▀ ▒█ ▒█ ▀▀▀▀ ▀   ▀ ▀▀▀  ▀  ▀   ▀   ▒█▄▄█ ▀▀▀▀   ▀  

Select an action:

    1. Create client by token
    2. Run clicker
    3. Create client by tg auth
    4. Migrate old sessions to clients
"""


def get_client_names() -> list[str]:
    client_names = glob.glob('clients/*.client')
    client_names = [os.path.splitext(os.path.basename(file))[0] for file in client_names]

    return client_names


def get_proxies() -> list[Proxy]:
    if settings.USE_PROXY_FROM_FILE:
        with open(file='bot/config/proxies.txt', encoding='utf-8-sig') as file:
            proxies = [Proxy.from_str(proxy=row.strip()).as_url for row in file]
    else:
        proxies = []

    return proxies


async def get_clients() -> list[str]:
    client_names = get_client_names()

    if not client_names:
        raise FileNotFoundError("Not found client files")

    clients = []
    for client_name in client_names:
        with open(f'clients/{client_name}.client', 'r') as file:
            clients.append(Client(client_name, file.read()))
    
    return clients


async def process() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--action', type=int, help='Action to perform')

    logger.info(f"Detected {len(get_client_names())} clients | {len(get_proxies())} proxies")

    action = parser.parse_args().action

    if not action:
        print(start_text)

        while True:
            action = input("> ")

            if not action.isdigit():
                logger.warning("Action must be number")
            elif action not in ['1', '2', '3', '4']:
                logger.warning("Action must be 1-4")
            else:
                action = int(action)
                break

    if action == 1:
        await register_client()
    elif action == 2:
        clients = await get_clients()

        await run_tasks(clients=clients)
    elif action == 3:
        await register_client_by_tg_auth()
    elif action == 4:
        await migrate_old_clients()


async def run_tasks(clients: list[Client]):
    proxies = get_proxies()
    proxies_cycle = cycle(proxies) if proxies else None
    tasks = [asyncio.create_task(run_tapper(client=client, proxy=next(proxies_cycle) if proxies_cycle else None))
             for client in clients]

    await asyncio.gather(*tasks)

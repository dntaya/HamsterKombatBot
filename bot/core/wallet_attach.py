import aiohttp

from bot.core.entities import AirDropTaskId
from bot.core.headers import headers
from bot.core.web_client import WebClient
from bot.utils import logger
from bot.utils.client import Client


async def attach_wallet(clients: list[Client]):
    wallet = input('\nEnter the wallet address: ')

    if not wallet:
        return None

    unpacked_wallet = await unpack_wallet(wallet)

    if unpacked_wallet is None:
        logger.error("Wallet not found")
        return None

    for client in clients:
        await attach_wallet_to_client(client=client, wallet=unpacked_wallet)


async def attach_wallet_to_client(client: Client, wallet: str):
    try:
        async with aiohttp.ClientSession(headers=headers) as http_client:
            web_client = WebClient(http_client=http_client, client=client, proxy=None)
            tasks = await web_client.get_airdrop_tasks()
            connect_ton_task = next(t for t in tasks if t.id == AirDropTaskId.CONNECT_TON_WALLET)
            if connect_ton_task.is_completed:
                logger.info(f"{client.name} | Wallet already attached")
            else:
                await web_client.attach_wallet(wallet=wallet)
                logger.success(f"{client.name} | Wallet attached")
    except aiohttp.ClientConnectorError as error:
        logger.error(f"Error while attaching wallet: {error}")


async def unpack_wallet(wallet: str) -> str | None:
    try:
        async with aiohttp.ClientSession(headers={"Accept": "application/json"}) as http_client:
            response = await http_client.get(url=f'https://toncenter.com/api/v2/unpackAddress?address={wallet}')
            json = await response.json()
            return json.get('result')
    except aiohttp.ClientConnectorError as error:
        logger.error(f"Error while unpacking wallet: {error}")
        return None

import aiohttp

from bot.core.entities import AirDropTaskId
from bot.core.headers import Headers
from bot.core.web_client import WebClient
from bot.utils import logger
from bot.utils.profile import Profile



async def deattach_wallet(profiles: Profile):
    wallet = input('\nEnter the wallet address: ')

    if not wallet:
        return None

    unpacked_wallet = await unpack_wallet(wallet)

    for profile in profiles:
        await attach_wallet_to_client(profile=profile, wallet=unpacked_wallet)        


async def attach_wallet_to_client(profile: Profile, wallet: str):
    unpacked_wallet = await unpack_wallet(wallet)

    if unpacked_wallet is None:
        logger.error("Wallet not found")
        return None

    headers = Headers()
    try:
        async with aiohttp.ClientSession(headers=headers) as http_client:
            web_client = WebClient(http_client=http_client, profile=profile)
            tasks = await web_client.get_airdrop_tasks()
            connect_ton_task = next(t for t in tasks if t.id == AirDropTaskId.CONNECT_TON_WALLET)
            if connect_ton_task.is_completed:
                logger.info(f"[{profile.name}] Wallet already attached")
            else:
                await web_client.attach_wallet(wallet=unpacked_wallet)
                logger.success(f"[{profile.name}] Wallet attached")
    except aiohttp.ClientConnectorError as error:
        logger.error(f"Error while attaching wallet: {error}")

async def detach_wallet(profile: Profile):
    headers = Headers()
    try:
        async with aiohttp.ClientSession(headers=headers) as http_client:
            web_client = WebClient(http_client=http_client, profile=profile)
            tasks = await web_client.delete_wallet()

    except aiohttp.ClientConnectorError as error:
        logger.error(f"Error while detaching wallet: {error}")

async def unpack_wallet(wallet: str) -> str | None:
    try:
        async with aiohttp.ClientSession() as http_client:
            response = await http_client.get(url=f'https://toncenter.com/api/v2/unpackAddress?address={wallet}')
            json = await response.json()
            return json.get('result')
    except aiohttp.ClientConnectorError as error:
        logger.error(f"Error while unpacking wallet: {error}")
        return None

async def add_referral(profile: Profile,  referrer: int):

    try:
        async with aiohttp.ClientSession(headers=Headers()) as http_client:
            web_client = WebClient(http_client=http_client, profile=profile)
            result = await web_client.add_referral(referrer)

            if result:
                logger.info(f"Referral {profile.name} successfully added to {result}")

            return result
    except aiohttp.ClientConnectorError as error:
        logger.error(f"Error while add referral: {error}")
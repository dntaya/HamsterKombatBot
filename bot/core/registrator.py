
from bot.utils import logger
import os

import asyncio
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestWebView
from bot.exceptions import InvalidSession
from pyrogram import Client
from urllib.parse import unquote
from bot.utils.fingerprint import FINGERPRINT
from bot.config import settings
import requests

async def register_client() -> None:
    client_name = input('\nEnter the client name (press Enter to exit): ')

    if not client_name:
        return None

    token = input('\nEnter the token (press Enter to exit): ')

    if not token:
        return None

    if os.path.isdir('clients') is False:
        os.mkdir('clients')

    f = open(f"clients/{client_name}.client", "a")
    f.write(token)
    f.close()

    logger.success(f'Client `{client_name}` added successfully')

async def create_token() -> str | None:
        try:
            tg_web_data = await get_tg_web_data()

            response = requests.post(url='https://api.hamsterkombat.io/auth/auth-by-telegram-webapp',
                                              json={"initDataRaw": tg_web_data, "fingerprint": FINGERPRINT})

            response_json = response.json()
            access_token = response_json['authToken']

            return access_token
        except Exception as error:
            logger.error(f"Unknown error while getting Access Token: {error}")


async def get_tg_web_data() -> str:
        tg_client = Client(
            name="hamster_bot",
            api_id=settings.API_ID,
            api_hash=settings.API_HASH
        )
        async with tg_client:
            user_data = await tg_client.get_me()
        
        try:
            if not tg_client.is_connected:
                try:
                    await tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession("hamster_bot")

            dialogs = tg_client.get_dialogs()
            async for dialog in dialogs:
                if dialog.chat and dialog.chat.username and dialog.chat.username == 'hamster_kombat_bot':
                    break

            while True:
                try:
                    peer = await tg_client.resolve_peer('hamster_kombat_bot')
                    break
                except FloodWait as fl:
                    return None

            web_view = await tg_client.invoke(RequestWebView(
                peer=peer,
                bot=peer,
                platform='android',
                from_bot_menu=False,
                url='https://hamsterkombat.io/'
            ))

            auth_url = web_view.url
            tg_web_data = unquote(
                string=unquote(
                    string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0]))

            if tg_client.is_connected:
                await tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)
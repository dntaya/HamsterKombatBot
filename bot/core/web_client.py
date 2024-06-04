import aiohttp
import traceback
import json as json_parser
from time import time
from better_proxy import Proxy
from bot.utils import logger
from bot.utils.client import Client
from bot.utils.scripts import escape_html
from bot.core.headers import additional_headers_for_empty_requests, createAdditionalHeadersForDataRequests
from bot.core.entities import Boost, Upgrade, Profile, Task, ProfileAndUpgrades
from enum import StrEnum

class Requests(StrEnum):
    CONFIG="https://api.hamsterkombat.io/clicker/config"
    ME_TELEGRAM="https://api.hamsterkombat.io/auth/me-telegram"
    TAP="https://api.hamsterkombat.io/clicker/tap"
    BOOSTS_FOR_BUY="https://api.hamsterkombat.io/clicker/boosts-for-buy"
    BUY_UPGRADE="https://api.hamsterkombat.io/clicker/buy-upgrade"
    UPGRADES_FOR_BUY="https://api.hamsterkombat.io/clicker/upgrades-for-buy"
    BUY_BOOST="https://api.hamsterkombat.io/clicker/buy-boost"
    CHECK_TASK="https://api.hamsterkombat.io/clicker/check-task"
    SELECT_EXCHANGE="https://api.hamsterkombat.io/clicker/select-exchange"
    LIST_TASKS="https://api.hamsterkombat.io/clicker/list-tasks"
    SYNC="https://api.hamsterkombat.io/clicker/sync"

class WebClient:
    def __init__(self, http_client: aiohttp.ClientSession, client: Client, proxy: str | None):
        self.http_client = http_client
        self.session_name = client.name
        self.http_client.headers["Authorization"] = f"Bearer {client.token}"
        self.proxy = proxy

    async def check_proxy(self, proxy: Proxy) -> None:
        try:
            response = await self.http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5))
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def get_profile_data(self) -> Profile | None:
        response = await self.make_request(Requests.SYNC)
        if response is not None:
            profile_data = response.get('clickerUser') or response.get('found', {}).get('clickerUser', {})
            return Profile(data=profile_data)

    async def get_tasks(self) -> list[Task]:
        response = await self.make_request(Requests.LIST_TASKS)
        if response is not None:
            return list(map(lambda d: Task(data=d), response['tasks']))
        else:
            return []

    async def select_exchange(self, exchange_id: str) -> bool:
        response = await self.make_request(Requests.SELECT_EXCHANGE, json={'exchangeId': exchange_id})
        return response is not None

    async def get_daily(self):
        response = await self.make_request(Requests.CHECK_TASK, json={'taskId': "streak_days"})
        return response is not None

    async def apply_boost(self, boost_id: str) -> Profile | None:
        response = await self.make_request(Requests.BUY_BOOST, json={'timestamp': time(), 'boostId': boost_id})
        if response is not None:
            profile_data = response.get('clickerUser') or response.get('found', {}).get('clickerUser', {})

            return Profile(data=profile_data)

    async def get_upgrades(self) -> list[Upgrade] | None:
        response = await self.make_request(Requests.UPGRADES_FOR_BUY)
        if response is not None:
            return list(map(lambda x: Upgrade(data=x), response['upgradesForBuy']))

    async def buy_upgrade(self, upgrade_id: str) -> ProfileAndUpgrades | None:
        response = await self.make_request(Requests.BUY_UPGRADE, json={'timestamp': time(), 'upgradeId': upgrade_id})
        if response is not None:
            profile_data = response.get('clickerUser') or response.get('found', {}).get('clickerUser', {})

            return ProfileAndUpgrades(profile=Profile(data=profile_data),
                                      upgrades=list(map(lambda x: Upgrade(data=x), profile_data['upgradesForBuy'])))

    async def get_boosts(self) -> list[Boost] | None:
        response = await self.make_request(Requests.BOOSTS_FOR_BUY)
        if response is not None:
            return list(map(lambda x: Boost(data=x), response['boostsForBuy']))

    async def send_taps(self, available_energy: int, taps: int) -> Profile | None:
        response = await self.make_request(Requests.TAP, json={'availableTaps': available_energy, 'count': taps, 'timestamp': time()})
        if response is not None:
            profile_data = response.get('clickerUser') or response.get('found', {}).get('clickerUser', {})

            return Profile(data=profile_data)
        
    async def get_me_telegram(self) -> None:
        await self.make_request(Requests.ME_TELEGRAM)
    
    async def get_config(self) -> None:
        await self.make_request(Requests.CONFIG)

    async def make_request(self, request: Requests, json: dict = {}) -> dict | None:
        response_text = ''
        try:
            headers = {}
            data = json_parser.dumps(json).encode('utf-8')
            if len(json) == 0:
                headers = additional_headers_for_empty_requests
            else:
                headers = createAdditionalHeadersForDataRequests(content_length=len(data))

            response = await self.http_client.post(url=request.value,
                                                   headers=headers,
                                                   data=data if len(json) > 0 else None)
            response_text = await response.text()
            if response.status != 422:
                response.raise_for_status()

            return json_parser.loads(response_text)
        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error in request: {error} | "
                         f"Response text: {escape_html(response_text)[:128]}")
            traceback.print_exc()
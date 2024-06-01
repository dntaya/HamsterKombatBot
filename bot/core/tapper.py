import operator
import asyncio
from time import time
from random import randint
from pyrogram import Client
from bot.utils import logger
from bot.exceptions import InvalidSession

import aiohttp
from aiohttp_proxy import ProxyConnector


from bot.config import settings
from bot.core.upgrade import Upgrade
from bot.core.web_client import WebClient

from .headers import headers


class Tapper:
    def __init__(self, web_client: WebClient) -> None:
        self.web_client = web_client
        self.balance = 0
        self.earn_per_hour = 0
        self.available_energy = 0
        self.taps_recover_per_sec = 0
        self.earn_per_tap = 0
        self.update_time = 0
        
    def update_profile_params(self, data: dict) -> None:
        self.earn_per_hour = data['earnPassivePerHour']
        self.balance = int(data['balanceCoins'])
        self.available_energy = data.get('availableTaps', 0)
        self.taps_recover_per_sec = data.get('tapsRecoverPerSec', 0)
        self.earn_per_tap = data.get('earnPerTap', 0)
        self.update_time = time()

    async def earn_money(self) -> bool:
        profile_data = await self.web_client()

        if not profile_data:
            return False
        
        exchange_id = profile_data.get('exchangeId')
        if not exchange_id:
            status = await self.web_client.select_exchange(exchange_id="bybit")
            if status is True:
                logger.success(f"{self.session_name} | Successfully selected exchange <y>Bybit</y>")

        last_passive_earn = profile_data['lastPassiveEarn']
        self.update_profile_params(data=profile_data)

        logger.info(f"{self.session_name} | Last passive earn: <g>+{last_passive_earn}</g> | "
                    f"Earn every hour: <y>{self.earn_per_hour}</y>")
        return True

    async def make_upgrades(self):
        while True:
            upgrades = await self.web_client.get_upgrades()

            available_upgrades = filter(lambda u: u.can_upgrade(), map(lambda data: Upgrade(data=data), upgrades))

            if not settings.WAIT_FOR_MOST_PROFIT_UPGRADES:
                available_upgrades = filter(lambda u: self.balance > u.price, available_upgrades)

            available_upgrades.sort(key=operator.attrgetter("significance"), reverse=True)

            if len(available_upgrades) == 0:
                logger.info(f"{self.session_name} | No available upgrades")
                break

            most_profit_upgrade = available_upgrades[0]

            if most_profit_upgrade.price > self.balance:
                logger.info(f"{self.session_name} | Not enough money for upgrade <e>{most_profit_upgrade.name}</e>")
                break

            logger.info(f"{self.session_name} | Sleep 3s before upgrade <e>{most_profit_upgrade.name}</e>")
            await asyncio.sleep(delay=3)

            status = await self.web_client.buy_upgrade(upgrade_id=most_profit_upgrade.id)
            if status is True:
                self.earn_per_hour += most_profit_upgrade.earn_per_hour
                self.balance -= most_profit_upgrade.price
                logger.success(
                    f"{self.session_name} | "
                    f"Successfully upgraded <e>{most_profit_upgrade.name}</e> to <m>{most_profit_upgrade.level}</m> lvl | "
                    f"Earn every hour: <y>{self.earn_per_hour}</y> (<g>+{most_profit_upgrade.earn_per_hour}</g>)")

                await asyncio.sleep(delay=1)

    async def apply_energy_boost(self) -> bool:
        boosts = await self.web_client.get_boosts()
        energy_boost = next((boost for boost in boosts if boost['id'] == 'BoostFullAvailableTaps'), {})
        if energy_boost.get("cooldownSeconds", 0) != 0 and energy_boost.get("level", 0) <= energy_boost.get("maxLevel", 0):
            return False

        profile_data = await self.web_client.apply_boost(boost_id="BoostFullAvailableTaps")
        if profile_data is not None:
            self.update_profile_params(data=profile_data)
            logger.success(f"{self.session_name} | Successfully apply energy boost")
            await asyncio.sleep(delay=1)

    async def make_taps(self) -> bool:
        max_taps = self.available_energy / self.earn_per_tap
        if max_taps < settings.MIN_AVAILABLE_TAPS:
            if self.apply_energy_boost() is False:
                logger.info(f"{self.session_name} | Not enough taps: {self.max_taps}/{settings.MIN_AVAILABLE_TAPS}")
                return True
            else:
                max_taps = self.available_energy / self.earn_per_tap
        
        taps = randint(a=0, b=max_taps)

        seconds_from_last_update = int(time() - self.update_time)
        energy_recovered = self.taps_recover_per_sec * seconds_from_last_update
        player_data = await self.web_client.send_taps(available_energy=self.available_energy + energy_recovered, taps=taps)

        if not player_data:
            return False
        
        new_balance = int(player_data.get('balanceCoins', 0))
        calc_taps = new_balance - self.balance
    
        self.update_profile_params(data=player_data)

        logger.success(f"{self.session_name} | Successful tapped! | "
                        f"Balance: <c>{self.balance}</c> (<g>+{calc_taps}</g>)")
        return True


    async def run(self) -> None:
        tasks_checking_time = 0
        earn_money_time = 0
        turbo_time = 0

        while True:
            try:
                # GET ACCESS TOKEN
                self.web_client.check_auth()
                
                # MONEY EARNING
                if time() - earn_money_time >= 3600:
                    money_earned = await self.earn_money()
                    if not money_earned:
                        continue
                    else:
                        earn_money_time = time()

                # DAILY TASKS
                if time() - tasks_checking_time >= 21600: # 6 hours
                    tasks = await self.web_client.get_tasks()
                    tasks_checking_time = time()

                    daily_task = tasks[-1]
                    rewards = daily_task['rewardsByDays']
                    is_completed = daily_task['isCompleted']
                    days = daily_task['days']

                    if is_completed is False:
                        status = await self.web_client.get_daily()
                        if status is True:
                            logger.success(f"{self.session_name} | Successfully get daily reward | "
                                            f"Days: <m>{days}</m> | Reward coins: {rewards[days - 1]['rewardCoins']}")
                            
                # UPGRADES
                if settings.AUTO_UPGRADE is True:
                    self.make_upgrades()

                
                # TAPPING
                if settings.AUTO_CLICKER is True:
                    self.make_taps()

                # TODO: sleep for recover full energy
                if available_energy < settings.MIN_AVAILABLE_ENERGY:
                    logger.info(f"{self.session_name} | Minimum energy reached: {available_energy}")
                    logger.info(f"{self.session_name} | Sleep {settings.SLEEP_BY_MIN_ENERGY}s")

                    await asyncio.sleep(delay=settings.SLEEP_BY_MIN_ENERGY)

                    continue

            except InvalidSession as error:
                raise error

            except Exception as error:
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await asyncio.sleep(delay=3)

            else:
                sleep_between_clicks = randint(a=settings.SLEEP_BETWEEN_TAP[0], b=settings.SLEEP_BETWEEN_TAP[1])

                if active_turbo is True:
                    sleep_between_clicks = 4

                logger.info(f"Sleep {sleep_between_clicks}s")
                await asyncio.sleep(delay=sleep_between_clicks)


async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
            web_client = WebClient(http_client=http_client, tg_client=tg_client, proxy=proxy)
            await Tapper(web_client=web_client).run()
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")

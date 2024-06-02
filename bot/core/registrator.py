
from bot.utils import logger


async def register_client() -> None:
    client_name = input('\nEnter the client name (press Enter to exit): ')

    if not client_name:
        return None

    token = input('\nEnter the token (press Enter to exit): ')

    if not token:
        return None

    f = open(f"clients/{client_name}.client", "a")
    f.write(token)
    f.close()

    logger.success(f'Client `{client_name}` added successfully')

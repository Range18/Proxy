import asyncio
import logging

from database import Base, engine
from services.listener import Listener
from services.logger_formatter import LoggerFormatter

handler = logging.StreamHandler()
handler.setFormatter(LoggerFormatter("%(asctime)s [%(levelname)s] %(message)s"))

logging.basicConfig(level=logging.INFO, handlers=[handler])

ADDRESS = "127.0.0.1"
PORT = 8080


async def main():
    Base.metadata.create_all(engine)

    proxy = Listener()
    server = await asyncio.start_server(proxy.handle_client, ADDRESS, PORT)

    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())

import asyncio

from connection_handler import handle_connection
from constants import CHUNK_SIZE
from http_parser import HttpParser


class Listener:
    def __init__(self):
        self.http_parser = HttpParser()

    async def handle_client(self, reader: asyncio.StreamReader,
                            writer: asyncio.StreamWriter):
        data = await reader.read(CHUNK_SIZE)
        if not data:
            writer.close()
            await writer.wait_closed()
            return

        request = self.http_parser.parse_http_request(data)

        host = request.headers.get("host")
        if not host:
            writer.close()
            await writer.wait_closed()
            return

        print(host)

        if ":" in host:
            address, port = host.split(":", 1)
            port = int(port)
        else:
            address, port = host, 80

        await handle_connection(address, port, request, reader, writer)

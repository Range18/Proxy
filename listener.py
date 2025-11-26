import asyncio
import logging

from blacklist_service import BlacklistService
from connection_handler import handle_connection
from constants import CHUNK_SIZE, GREEN
from http_parser import HttpParser

logger = logging.getLogger("connection_handler")


class Listener:
    def __init__(self):
        self.http_parser = HttpParser()
        self.blacklist_service = BlacklistService()

    async def handle_client(self, reader: asyncio.StreamReader,
                            writer: asyncio.StreamWriter):
        data = await self.read_full_request(reader)
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

        if ":" in host:
            address, port = host.split(":", 1)
            port = int(port)
        else:
            address, port = host, 80

        if self.blacklist_service.is_banned(address, port):
            #TODO send rofls BAN WINDOW
            writer.close()
            await writer.wait_closed()
            return

        peer_ip, peer_port = writer.get_extra_info("peername")
        logger.info(
            f"New connection: from {peer_ip}:{peer_port} to {address}:{port} {request.method} {request.path}")
        await handle_connection(address, port, request, reader, writer)

    async def read_full_request(self, reader):
        buffer = b""
        while b"\r\n\r\n" not in buffer:
            chunk = await reader.read(CHUNK_SIZE)
            if not chunk:
                break
            buffer += chunk
        return buffer

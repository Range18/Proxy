import asyncio
import logging

from services.auth_service import AuthService
from services.blacklist_service import BlacklistService
from constants import CHUNK_SIZE, RED, TRAFFIC_EXCEEDED_BODY
from services.connection_handler import ConnectionHandler
from services.http_parser import HttpParser
from services.user_service import UserService

logger = logging.getLogger("listener")


class Listener:
    def __init__(self):
        self.http_parser = HttpParser()
        self.blacklist_service = BlacklistService()
        self.auth_service = AuthService()
        self.user_service = UserService()
        self.connection_handler = ConnectionHandler()

        with open("./public/blocked-page.html", "r", encoding="utf-8") as f:
            self.ban_page_html = f.read()

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ):
        data = await self.read_full_request(reader)
        if not data:
            writer.close()
            await writer.wait_closed()
            return

        peer_ip, peer_port = writer.get_extra_info("peername")
        request = self.http_parser.parse_http_request(data)
        user, ok = self.auth_service.check_auth(request, peer_ip)
        if not ok:
            response = (
                "HTTP/1.1 407 Proxy Authentication Required\r\n"
                'Proxy-Authenticate: Basic realm="Proxy"\r\n'
                "Content-Length: 0\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode("ascii")

            writer.write(response)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        if self.user_service.check_data_overdraft(
            user, len(request.original_request_encoded)
        ):
            logger.info(
                f"{RED}Traffic limit exceeded: user={user.username}, "
                f"ip={peer_ip}, used={len(request.body)} bytes"
            )

            body = TRAFFIC_EXCEEDED_BODY

            headers = (
                "HTTP/1.1 509 Bandwidth Limit Exceeded\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode("ascii")

            writer.write(headers + body)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

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
            logger.info(
                f"{RED}Blocked connection: from {peer_ip}:{peer_port} to {address}:{port} "
                f"{request.method} {request.path}"
            )

            body = self.ban_page_html.encode("utf-8")

            headers = (
                "HTTP/1.1 403 Forbidden\r\n"
                "Content-Type: text/html; charset=utf-8\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode("ascii")

            writer.write(headers + body)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            return

        logger.info(
            f"New connection: from {peer_ip}:{peer_port} to {address}:{port} "
            f"{request.method} {request.path}"
        )

        await self.connection_handler.handle_connection(
            user, address, port, request, reader, writer
        )

    async def read_full_request(self, reader):
        buffer = b""
        while b"\r\n\r\n" not in buffer:
            chunk = await reader.read(CHUNK_SIZE)
            if not chunk:
                break
            buffer += chunk
        return buffer

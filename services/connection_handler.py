import asyncio
import logging

from constants import CHUNK_SIZE, TRAFFIC_EXCEEDED_BODY, RED
from models.http_request import HttpRequest
from models.user_model import User
from services.user_service import UserService

logger = logging.getLogger("connection_handler")


class ConnectionHandler:
    def __init__(self):
        self.user_service = UserService()

    async def handle_connection(
        self,
        user: User,
        address: str,
        port: int,
        request: HttpRequest,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
        try:
            remote_reader, remote_writer = await asyncio.open_connection(address, port)
        except Exception as e:
            print("connect error:", e)
            writer.close()
            await writer.wait_closed()
            return

        is_connect = request.method == "CONNECT"

        if is_connect:
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            await writer.drain()
        else:
            remote_writer.write(request.original_request_encoded)
            await remote_writer.drain()

        await asyncio.gather(
            # клиент -> сервер
            self.relay(user, reader, remote_writer, writer, is_connect),
            # сервер -> клиент
            self.relay(user, remote_reader, writer, writer, is_connect),
            return_exceptions=True,
        )

        try:
            remote_writer.close()
            await remote_writer.wait_closed()
        except:
            pass

        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass

    async def relay(
        self,
        user: User,
        src_reader: asyncio.StreamReader,
        dst_writer: asyncio.StreamWriter,
        client_writer: asyncio.StreamWriter,
        is_connect: bool,
    ):
        try:
            while True:
                chunk = await src_reader.read(CHUNK_SIZE)
                if not chunk:
                    break

                if self.user_service.check_data_overdraft(user, len(chunk)):
                    logger.info(
                        f"{RED}Traffic limit exceeded: user={user.username}, "
                        f"ip={user.ip}, used={len(chunk)} bytes"
                    )

                    if not is_connect:
                        body = TRAFFIC_EXCEEDED_BODY

                        headers = (
                            "HTTP/1.1 509 Bandwidth Limit Exceeded\r\n"
                            "Content-Type: text/html; charset=utf-8\r\n"
                            f"Content-Length: {len(body)}\r\n"
                            "Connection: close\r\n"
                            "\r\n"
                        ).encode("ascii")

                        try:
                            client_writer.write(headers + body)
                            await client_writer.drain()
                        except:
                            pass
                    try:
                        client_writer.close()
                        await client_writer.wait_closed()
                    except:
                        pass

                    try:
                        dst_writer.close()
                        await dst_writer.wait_closed()
                    except:
                        pass

                    break

                dst_writer.write(chunk)
                await dst_writer.drain()

        except ConnectionResetError:
            pass
        except Exception as e:
            print("relay error:", e)
        finally:
            try:
                dst_writer.write_eof()
            except:
                pass

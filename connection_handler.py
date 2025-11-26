import asyncio

from constants import CHUNK_SIZE
from http_request import HttpRequest


class ConnectionHandler:
    async def handle_connection(self, address: str, port: int, request: HttpRequest, reader: asyncio.StreamReader,
                                writer: asyncio.StreamWriter):
        try:
            remote_reader, remote_writer = await asyncio.open_connection(
                address, port
            )
        except Exception as e:
            print("connect error:", e)
            writer.close()
            await writer.wait_closed()
            return

        remote_writer.write(request.original_request_encoded)
        await remote_writer.drain()

        await asyncio.gather(
            self.relay(reader, remote_writer),
            self.relay(remote_reader, writer),
        )

        remote_writer.close()
        writer.close()
        await remote_writer.wait_closed()
        await writer.wait_closed()

    async def relay(self, src_reader: asyncio.StreamReader,
                    dst_writer: asyncio.StreamWriter):
        try:
            while True:
                chunk = await src_reader.read(CHUNK_SIZE)
                if not chunk:
                    break
                dst_writer.write(chunk)
                await dst_writer.drain()
        except Exception as e:
            print("relay error:", e)

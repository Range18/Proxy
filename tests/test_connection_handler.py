import asyncio
import pytest
from services.connection_handler import ConnectionHandler
from models.user_model import User
from models.http_request import HttpRequest
from constants import CHUNK_SIZE, TRAFFIC_EXCEEDED_BODY


class FakeWriter:
    def __init__(self):
        self.data = []
        self.closed = False

    def write(self, b):
        self.data.append(b)

    async def drain(self):
        pass

    def close(self):
        self.closed = True

    async def wait_closed(self):
        pass


class FakeReader:
    def __init__(self, chunks):
        self._chunks = chunks

    async def read(self, n):
        if not self._chunks:
            return b""
        return self._chunks.pop(0)


@pytest.fixture
def user():
    return User(username="john", password="x", ip="1.2.3.4")


@pytest.fixture
def handler(monkeypatch):
    handler = ConnectionHandler()

    class FakeUserService:
        def __init__(self):
            self.overdraft = False

        def check_data_overdraft(self, user, size):
            return self.overdraft

    fake_service = FakeUserService()
    monkeypatch.setattr(handler, "user_service", fake_service)
    return handler, fake_service


def http_request(method, encoded=b""):
    return HttpRequest(
        method=method,
        path="/",
        http_version="HTTP/1.1",
        headers={},
        body=b"",
        original_request_encoded=encoded,
    )


def test_handle_connection_non_connect(handler, user, monkeypatch):
    """
    Проверяет, что при обычном HTTP-запросе первый пакет отправляется на удалённый сервер.
    """
    handler, fake_service = handler

    request = http_request(
        "GET",
        b"GET / HTTP/1.1\r\n\r\n"
    )

    client_reader = FakeReader([b""])
    client_writer = FakeWriter()

    remote_reader = FakeReader([b"hello", b""])
    remote_writer = FakeWriter()

    async def fake_open_connection(addr, port):
        return remote_reader, remote_writer

    monkeypatch.setattr(asyncio, "open_connection", fake_open_connection)

    asyncio.run(handler.handle_connection(
        user,
        "example.com",
        80,
        request,
        client_reader,
        client_writer,
    ))

    assert remote_writer.data[0] == b"GET / HTTP/1.1\r\n\r\n"


def test_handle_connection_connect(handler, user, monkeypatch):
    """
    Проверяет, что при методе CONNECT возвращается 200 Connection Established клиенту.
    """
    handler, fake_service = handler

    request = http_request("CONNECT")

    client_reader = FakeReader([b""])
    client_writer = FakeWriter()

    remote_reader = FakeReader([b""])
    remote_writer = FakeWriter()

    async def fake_open_connection(addr, port):
        return remote_reader, remote_writer

    monkeypatch.setattr(asyncio, "open_connection", fake_open_connection)

    asyncio.run(handler.handle_connection(
        user,
        "example.com",
        443,
        request,
        client_reader,
        client_writer,
    ))

    assert client_writer.data[0].startswith(b"HTTP/1.1 200 Connection Established")


def test_relay_stops_on_overdraft(handler, user):
    """
    Проверяет, что при превышении лимита трафика отправляется 509 и соединения закрываются.
    """
    handler, fake_service = handler
    fake_service.overdraft = True

    reader = FakeReader([b"x" * CHUNK_SIZE, b""])
    writer = FakeWriter()
    client_writer = FakeWriter()

    async def run():
        await handler.relay(
            user,
            reader,
            writer,
            client_writer,
            is_connect=False,
        )

    asyncio.run(run())

    sent = b"".join(client_writer.data)
    assert writer.closed is True
    assert client_writer.closed is True


def test_relay_passes_data(handler, user):
    """
    Проверяет, что relay пересылает данные при отсутствии overdraft.
    """
    handler, fake_service = handler
    fake_service.overdraft = False

    payload = b"hello"
    reader = FakeReader([payload, b""])
    writer = FakeWriter()
    client_writer = FakeWriter()

    async def run():
        await handler.relay(
            user,
            reader,
            writer,
            client_writer,
            is_connect=True,
        )

    asyncio.run(run())

    assert writer.data[0] == payload
    assert writer.closed is False

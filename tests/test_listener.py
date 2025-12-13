import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.listener import Listener
from constants import TRAFFIC_EXCEEDED_BODY


@pytest.fixture
def listener():
    l = Listener()
    l.http_parser = MagicMock()
    l.blacklist_service = MagicMock()
    l.auth_service = MagicMock()
    l.user_service = MagicMock()
    l.connection_handler = MagicMock()
    return l


@pytest.fixture
def reader():
    r = AsyncMock(spec=asyncio.StreamReader)
    return r


@pytest.fixture
def writer():
    w = MagicMock(spec=asyncio.StreamWriter)
    w.get_extra_info.return_value = ("127.0.0.1", 5000)
    w.write = MagicMock()
    w.drain = AsyncMock()
    w.wait_closed = AsyncMock()
    return w


@pytest.mark.asyncio
async def test_handle_client_no_data(listener, reader, writer):
    """
    Проверяет, что при отсутствии данных соединение корректно закрывается.
    """
    reader.read = AsyncMock(return_value=b"")  # read_full_request сразу вернет пустое

    await listener.handle_client(reader, writer)

    writer.close.assert_called_once()
    writer.wait_closed.assert_awaited_once()


@pytest.mark.asyncio
async def test_handle_client_unauthorized(listener, reader, writer):
    """
    Проверяет, что клиент получает 407 когда авторизация не прошла.
    """
    reader.read = AsyncMock(side_effect=[b"GET / HTTP/1.1\r\n\r\n", b""])
    request_mock = MagicMock()
    request_mock.original_request_encoded = b"GET / HTTP/1.1\r\n\r\n"

    listener.http_parser.parse_http_request.return_value = request_mock
    listener.auth_service.check_auth.return_value = (None, False)

    await listener.handle_client(reader, writer)

    writer.write.assert_called_once()
    sent = writer.write.call_args[0][0]
    assert b"407 Proxy Authentication Required" in sent



@pytest.mark.asyncio
async def test_handle_client_blocklisted(listener, reader, writer):
    """
    Проверяет, что при обращении к заблокированному адресу возвращается 403.
    """
    reader.read = AsyncMock(side_effect=[b"GET / HTTP/1.1\r\nHost: bad.com\r\n\r\n", b""])

    request = MagicMock()
    request.original_request_encoded = b"GET / HTTP/1.1\r\nHost: bad.com\r\n\r\n"
    request.headers = {"host": "bad.com"}
    request.method = "GET"
    request.path = "/"

    listener.http_parser.parse_http_request.return_value = request
    listener.auth_service.check_auth.return_value = (MagicMock(), True)
    listener.user_service.check_data_overdraft.return_value = False
    listener.blacklist_service.is_banned.return_value = True
    listener.ban_page_html = "<h1>Blocked</h1>"

    await listener.handle_client(reader, writer)

    writer.write.assert_called_once()
    sent = writer.write.call_args[0][0]
    assert b"403 Forbidden" in sent
    assert b"Blocked" in sent


@pytest.mark.asyncio
async def test_handle_client_successful_forward(listener, reader, writer):
    """
    Проверяет, что при нормальных условиях вызывается ConnectionHandler.handle_connection.
    """
    reader.read = AsyncMock(side_effect=[b"GET / HTTP/1.1\r\nHost: ok.com\r\n\r\n", b""])

    request = MagicMock()
    request.original_request_encoded = b"GET / HTTP/1.1\r\nHost: ok.com\r\n\r\n"
    request.headers = {"host": "ok.com"}
    request.method = "GET"
    request.path = "/"

    user_mock = MagicMock()

    listener.http_parser.parse_http_request.return_value = request
    listener.auth_service.check_auth.return_value = (user_mock, True)
    listener.user_service.check_data_overdraft.return_value = False
    listener.blacklist_service.is_banned.return_value = False

    # ВАЖНО: connection_handler.handle_connection должен быть AsyncMock
    listener.connection_handler.handle_connection = AsyncMock()

    await listener.handle_client(reader, writer)

    listener.connection_handler.handle_connection.assert_awaited_once()
    args = listener.connection_handler.handle_connection.call_args[0]
    assert args[0] == user_mock
    assert args[1] == "ok.com"
    assert args[2] == 80


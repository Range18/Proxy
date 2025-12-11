import pytest
from services.http_parser import HttpParser
from models.http_request import HttpRequest


parser = HttpParser()


def test_parse_valid_get_request():
    """
    Проверяет корректный парсинг простого GET запроса.
    """
    raw = (
        b"GET /index.html HTTP/1.1\r\n"
        b"Host: example.com\r\n"
        b"User-Agent: Test\r\n"
        b"\r\n"
    )

    req = parser.parse_http_request(raw)

    assert isinstance(req, HttpRequest)
    assert req.method == "GET"
    assert req.path == "/index.html"
    assert req.http_version == "HTTP/1.1"
    assert req.headers["host"] == "example.com"
    assert req.headers["user-agent"] == "Test"
    assert req.body == b""


def test_parse_request_with_body():
    """
    Проверяет, что тело запроса корректно извлекается.
    """
    raw = (
        b"POST /submit HTTP/1.1\r\n"
        b"Host: example.com\r\n"
        b"Content-Type: text/plain\r\n"
        b"\r\n"
        b"hello world"
    )

    req = parser.parse_http_request(raw)

    assert req.method == "POST"
    assert req.path == "/submit"
    assert req.body == b"hello world"


def test_parse_request_missing_separator():
    """
    Проверяет, что при отсутствии \r\n\r\n выбрасывается ошибка.
    """
    raw = b"GET / HTTP/1.1\r\nHost: x"

    with pytest.raises(ValueError):
        parser.parse_http_request(raw)


def test_parse_empty_request_line():
    """
    Проверяет, что пустая строка запроса приводит к ошибке.
    """
    raw = b"\r\n\r\n"

    with pytest.raises(ValueError):
        parser.parse_http_request(raw)


def test_parse_malformed_request_line():
    """
    Проверяет, что некорректная request line с недостатком элементов вызывает ошибку.
    """
    raw = (
        b"GET\r\n"
        b"Host: example.com\r\n"
        b"\r\n"
    )

    with pytest.raises(ValueError):
        parser.parse_http_request(raw)


def test_parse_headers_merging_duplicates():
    """
    Проверяет, что дублирующиеся заголовки объединяются в одну строку через запятую.
    """
    raw = (
        b"GET / HTTP/1.1\r\n"
        b"Cookie: a=1\r\n"
        b"Cookie: b=2\r\n"
        b"\r\n"
    )

    req = parser.parse_http_request(raw)

    assert req.headers["cookie"] == "a=1, b=2"


def test_ignore_header_without_colon():
    """
    Проверяет, что строки без ':' игнорируются.
    """
    raw = (
        b"GET / HTTP/1.1\r\n"
        b"BrokenHeader\r\n"
        b"Host: example.com\r\n"
        b"\r\n"
    )

    req = parser.parse_http_request(raw)

    assert "brokenheader" not in req.headers
    assert req.headers["host"] == "example.com"


def test_parse_path_with_spaces():
    """
    Проверяет корректный разбор path, содержащего пробелы.
    """
    raw = (
        b"GET /search?q=hello world HTTP/1.1\r\n"
        b"Host: example.com\r\n"
        b"\r\n"
    )

    req = parser.parse_http_request(raw)

    assert req.path == "/search?q=hello world"

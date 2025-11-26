import json


class HttpRequest:
    def __init__(
            self,
            method: str,
            path: str,
            http_version: str,
            headers: dict[str, str],
            body: bytes,
            original_request_encoded: bytes,
    ):
        self.method = method
        self.path = path
        self.http_version = http_version
        self.headers = headers
        self.body = body
        self.original_request_encoded = original_request_encoded

    def get_header(self, name: str, default: str | None = None) -> str | None:
        return self.headers.get(name.lower(), default)

    @property
    def host(self) -> str | None:
        return self.get_header("host")

    def text(self, encoding: str = "utf-8", errors: str = "replace") -> str:
        """Тело как текст."""
        return self.body.decode(encoding, errors)

    def json(self, encoding: str = "utf-8"):
        """Тело как JSON-объект (dict/list)."""
        return json.loads(self.body.decode(encoding))

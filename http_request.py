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

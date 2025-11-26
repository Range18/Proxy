from typing import Dict, List
from http_request import HttpRequest


class HttpParser:
    def parse_http_request(self, encoded_data: bytes) -> HttpRequest:
        separator = b"\r\n\r\n"
        sep_position = encoded_data.find(separator)
        if sep_position == -1:
            raise ValueError("Invalid HTTP request: no header/body separator")

        headers_bytes = encoded_data[:sep_position]
        body_bytes = encoded_data[sep_position + len(separator):]

        headers_text = headers_bytes.decode("iso-8859-1")

        header_lines = headers_text.split("\r\n")
        if not header_lines or not header_lines[0]:
            raise ValueError("Invalid HTTP request: empty request line")

        http_line = header_lines[0]
        headers_dict = self.parse_headers(header_lines[1:])

        http_line_parts = http_line.split(" ")
        if len(http_line_parts) < 3:
            raise ValueError("Invalid request line")

        method = http_line_parts[0]
        http_version = http_line_parts[-1]
        path = " ".join(http_line_parts[1:-1])

        return HttpRequest(method, path, http_version, headers_dict, body_bytes, encoded_data)

    def parse_headers(self, headers: List[str]) -> Dict[str, str]:
        headers_dict: Dict[str, str] = {}

        for header in headers:
            if not header:
                continue

            if ":" not in header:
                continue

            key, value = header.split(":", maxsplit=1)
            key = key.strip().lower()
            value = value.strip()

            if key in headers_dict:
                headers_dict[key] += ", " + value
            else:
                headers_dict[key] = value

        return headers_dict

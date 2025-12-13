import json
import os
import fnmatch
from urllib.parse import urlparse


class BlacklistService:
    def __init__(self):
        if os.path.exists("./blacklist.json"):
            with open("./blacklist.json", "r", encoding="utf-8") as f:
                self.blacklist = json.load(f)
        else:
            self.blacklist = {}

    def _host(self, address: str) -> str:
        if "://" in address:
            address = urlparse(address).hostname or address
        address = address.split("/")[0]
        return address.lower().strip(".")

    def _match(self, host: str, pattern: str) -> bool:
        pattern = pattern.lower()
        if pattern.startswith("*."):
            base = pattern[2:]
            return host == base or host.endswith("." + base)
        return fnmatch.fnmatch(host, pattern)

    def is_banned(self, address: str, port: int = 80) -> bool:
        host = self._host(address)

        for pattern, ports in self.blacklist.items():
            if self._match(host, pattern):
                if "*" in ports:
                    return True
                return port in ports

        return False

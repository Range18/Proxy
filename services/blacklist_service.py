import json
import os
import fnmatch


class BlacklistService:
    def __init__(self):
        if os.path.exists("../blacklist.json"):
            with open("../blacklist.json", "r") as f:
                self.blacklist = json.load(f)
        else:
            self.blacklist = {}

    def is_banned(self, address: str, port: int = 80) -> bool:
        for pattern, ports in self.blacklist.items():
            if fnmatch.fnmatch(address, pattern):
                if "*" in ports:
                    return True
                return port in ports

        return False

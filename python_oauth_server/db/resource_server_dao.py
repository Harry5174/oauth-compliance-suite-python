import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RS_FILE = BASE_DIR / "resources" / "resource_servers.json"

class ResourceServerDao:
    _servers = None

    @classmethod
    def _load_servers(cls):
        if cls._servers is None:
            with open(RS_FILE, "r") as f:
                data = json.load(f)
                cls._servers = {rs["id"]: rs for rs in data}
        return cls._servers

    @classmethod
    def get(cls, rs_id: str):
        servers = cls._load_servers()
        return servers.get(rs_id)
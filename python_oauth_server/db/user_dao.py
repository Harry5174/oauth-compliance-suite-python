import json
import os
from pathlib import Path

# Resolve the path to the resources directory
BASE_DIR = Path(__file__).resolve().parent.parent
USERS_FILE = BASE_DIR / "resources" / "users.json"

class UserDao:
    _users = None

    @classmethod
    def _load_users(cls):
        if cls._users is None:
            with open(USERS_FILE, "r") as f:
                data = json.load(f)
                # Index by loginId for fast lookups
                cls._users = {user["loginId"]: user for user in data}
        return cls._users

    @classmethod
    def get_by_login_id(cls, login_id: str):
        users = cls._load_users()
        return users.get(login_id)

    @classmethod
    def get_by_subject(cls, subject: str):
        users = cls._load_users()
        # Search the loaded users for a matching subject ID
        for user in users.values():
            if user["subject"] == subject:
                return user
        return None
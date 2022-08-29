import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Optional


def digest_password(password_plain: str) -> str:
    return hashlib.sha256(password_plain.encode()).hexdigest()


@dataclass(frozen=True)
class User:
    username: str
    password_digest: str
    permissions: list[str]

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        return cls(
            username=data['username'],
            password_digest=data.get('password_digest') or digest_password(data['password_plain']),
            permissions=data['permissions'],
        )


def load_users(filename: str = 'users.json') -> dict[str, User]:
    with open(filename) as file:
        return {
            (user := User.from_dict(d)).username: user
            for d in json.load(file)['users']
        }


USERS = load_users('users.json')


def authenticate(username: str, password: str) -> Optional[User]:
    user = USERS.get(username)
    if not user:
        # user not found
        return None

    if not secrets.compare_digest(digest_password(password), user.password_digest):
        # wrong password
        return None

    # all ok
    return user

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
    roles: list[str]

    @classmethod
    def from_dict(cls, d: dict) -> 'User':
        return cls(
            username=d['username'],
            password_digest=d.get('password_digest') or digest_password(d['password_plain']),
            roles=d['roles'],
        )


def load_users(fn: str = 'users.json') -> dict[str, User]:
    with open(fn) as f:
        return {
            (user := User.from_dict(d)).username: user
            for d in json.load(f)['users']
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

import hashlib
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


# TODO: load users from a file
USERS = [
    User('tom', digest_password('hunter2'), ['publisher', 'consumer']),
    User('guest', digest_password('guest'), ['publisher']),
    User('raspberry', digest_password('loop'), ['consumer']),
]

USERS_DICT = {user.username: user for user in USERS}


def authenticate(username: str, password: str) -> Optional[User]:
    user = USERS_DICT.get(username)
    if not user:
        # user not found
        return None

    if not secrets.compare_digest(digest_password(password), user.password_digest):
        # wrong password
        return None

    # all ok
    return user

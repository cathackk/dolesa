import hashlib
import os
import secrets
import string
from dataclasses import dataclass
from typing import Optional

import yaml

from dolesa.exceptions import ConfigurationException

MIN_PASSWORD_LENGTH = 8
VALID_PERMISSIONS = frozenset(['send', 'receive', 'list'])
PASSWORD_HEXDIGEST_LENGTH = 64  # SHA-256

# overwrites settings in users.yaml
ADMIN_USERNAME = os.environ.get('DOLESA_ADMIN_USERNAME')
ADMIN_PASSWORD = os.environ.get('DOLESA_ADMIN_PASSWORD')


def digest_password(password_plain: str) -> str:
    return hashlib.sha256(password_plain.encode()).hexdigest().lower()


@dataclass(frozen=True)
class User:
    username: str
    password_digest: str
    permissions: list[str]

    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """
        >>> User.from_dict({
        ...     'username': 'bob',
        ...     'password_plain': 'pass1234',
        ...     'permissions': ['send', 'receive']}
        ... )  # doctest: +NORMALIZE_WHITESPACE
        User(username='bob',
             password_digest='bd94dcda26fccb4e68d6a31f9b5aac0b571ae266d822620e901ef7ebe3a11d4f',
             permissions=['send', 'receive'])

        >>> User.from_dict({})
        Traceback (most recent call last):
        ...
        dolesa.exceptions.ConfigurationException: no username

        >>> User.from_dict({'username': ''})
        Traceback (most recent call last):
        ...
        dolesa.exceptions.ConfigurationException: username must not be empty

        >>> User.from_dict({'username': 'bob'})
        Traceback (most recent call last):
        ...
        dolesa.exceptions.ConfigurationException: bob: no `password_digest` or `password_plain`

        >>> User.from_dict({'username': 'bob', 'password_plain': '123'})
        Traceback (most recent call last):
        ...
        dolesa.exceptions.ConfigurationException: bob: password must be at least 8 characters long

        >>> User.from_dict({'username': 'bob', 'password_digest': 'abcd'})
        ... # doctest: +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
        ...
        dolesa.exceptions.ConfigurationException:
        bob: password digest must be exactly 64 characters long

        >>> User.from_dict({'username': 'bob', 'password_digest': '0'*63 + 'X'})
        ... # doctest: +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
        ...
        dolesa.exceptions.ConfigurationException:
        bob: nonhexadecimal characters found in password digest

        >>> User.from_dict({
        ...     'username': 'bob',
        ...     'password_plain': '12345678',
        ...     'permissions': ['send', 'something']
        ... })  # doctest: +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
        ...
        dolesa.exceptions.ConfigurationException:
        bob: invalid permission(s) ['something']; valid permissions are: ['list', 'receive', 'send']
        """

        # username
        username = data.pop('username', None)
        if username is None:
            raise ConfigurationException('no username')
        if not username:
            raise ConfigurationException('username must not be empty')

        # password
        if 'password_digest' in data:
            password_digest = data.pop('password_digest').strip().lower()
            if len(password_digest) != PASSWORD_HEXDIGEST_LENGTH:
                raise ConfigurationException(
                    f'{username}: password digest must be '
                    f'exactly {PASSWORD_HEXDIGEST_LENGTH} characters long'
                )
            if set(password_digest) - set(string.hexdigits):
                raise ConfigurationException(
                    f'{username}: nonhexadecimal characters found in password digest'
                )
            if 'password_plain' in data:
                raise ConfigurationException(
                    f'{username}: cannot define both `password_digest` and `password_plain`'
                )
        elif 'password_plain' in data:
            password_plain = data.pop('password_plain')
            if len(password_plain) < MIN_PASSWORD_LENGTH:
                raise ConfigurationException(
                    f'{username}: password must be at least {MIN_PASSWORD_LENGTH} characters long'
                )
            password_digest = digest_password(password_plain)
        else:
            raise ConfigurationException(f'{username}: no `password_digest` or `password_plain`')

        # permissions
        permissions = data.pop('permissions', None)
        if permissions is None:
            raise ConfigurationException(f'{username}: no permissions')
        if extra_permissions := sorted(set(permissions) - VALID_PERMISSIONS):
            raise ConfigurationException(
                f'{username}: invalid permission(s) {extra_permissions}; '
                f'valid permissions are: {sorted(VALID_PERMISSIONS)}'
            )

        # config keys
        if extra_kwargs := sorted(data.keys()):
            raise ConfigurationException(f'{username}: invalid configuration key(s) {extra_kwargs}')

        return cls(
            username=username,
            password_digest=password_digest,
            permissions=permissions,
        )


def load_users(filename: str = 'config/users.yaml') -> dict[str, User]:
    with open(filename) as file:
        users_config = yaml.safe_load(file)['users']
        users = {(user := User.from_dict(d)).username: user for d in users_config}

        if ADMIN_USERNAME and ADMIN_PASSWORD:
            users[ADMIN_USERNAME] = User(
                username=ADMIN_USERNAME,
                password_digest=digest_password(ADMIN_PASSWORD),
                permissions=sorted(VALID_PERMISSIONS),
            )

        return users


USERS = load_users()


def authenticate(username: str, password: str) -> Optional['User']:
    user = USERS.get(username)
    if not user:
        # user not found
        return None

    if not secrets.compare_digest(digest_password(password), user.password_digest):
        # wrong password
        return None

    # all ok
    return user

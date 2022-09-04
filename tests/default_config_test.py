import os
import random
from http import HTTPStatus
from typing import Optional

import requests

ADMIN_USERNAME = os.environ['DOLESA_ADMIN_USERNAME']
ADMIN_PASSWORD = os.environ['DOLESA_ADMIN_PASSWORD']
# TODO: load from env
HOST = 'http://localhost:8080'


def session(username: Optional[str] = None, password: Optional[str] = None) -> requests.Session:
    sess = requests.Session()
    sess.auth = (username or ADMIN_USERNAME, password or ADMIN_PASSWORD)
    return sess


def test_health() -> None:
    response = session().get(f'{HOST}/health')
    assert response.ok
    assert response.json() == {'status': 'running'}


def test_health__unauthenticated() -> None:
    response = requests.get(f'{HOST}/health')
    assert response.ok
    assert response.json() == {'status': 'running'}


def test_queues_list() -> None:
    response = session().get(f'{HOST}/queues')
    assert response.ok
    assert response.json() == {'queues': ['default'], 'default_queue': 'default'}


def test_queues_list__unauthenticated() -> None:
    response = requests.get(f'{HOST}/queues')
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_queues_list__wrong_password() -> None:
    response = session(password='somethingwrong').get(f'{HOST}/queues')
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_queues_list__wrong_username() -> None:
    response = session(username='johnny').get(f'{HOST}/queues')
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_get_queue_definition() -> None:
    response = session().get(f'{HOST}/queues/default')
    assert response.ok
    assert response.json() == {'queue': 'default', 'schema': {}}


def test_get_queue_info__wrong_queue_name() -> None:
    response = session().get(f'{HOST}/queues/xxx')
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json() == {
        'error': "queue not found",
        'description': "queue 'xxx' is not configured",
    }


def test_send_receive__default_endpoint() -> None:
    my_message = {'text': 'sending to default endpoint', 'num': random.randint(1, 1000)}

    response_send = session().post(f'{HOST}/send', json=my_message)
    assert response_send.status_code == HTTPStatus.ACCEPTED
    assert response_send.json() == {'routed': 1}

    response_receive = session().post(f'{HOST}/receive')
    assert response_receive.status_code == HTTPStatus.OK

    assert response_receive.json()['remaining'] == 0
    received = response_receive.json()['received']
    assert len(received) == 1
    (msg,) = received
    assert isinstance(msg.pop('ts'), int)
    assert msg == {
        'message': my_message,
        'queue': 'default',
        'sender': ADMIN_USERNAME,
    }


def test_send_receive__explicit_endpoint() -> None:
    my_message = {'text': 'sending to explicit endpoint', 'num': random.randint(1, 1000)}

    response_send = session().post(f'{HOST}/queues/default/send', json=my_message)
    assert response_send.status_code == HTTPStatus.ACCEPTED
    assert response_send.json() == {'routed': 1}

    response_receive = session().post(f'{HOST}/queues/default/receive')
    assert response_receive.status_code == HTTPStatus.OK

    assert response_receive.json()['remaining'] == 0
    received = response_receive.json()['received']
    assert len(received) == 1
    (msg,) = received
    assert isinstance(msg.pop('ts'), int)
    assert msg == {
        'message': my_message,
        'queue': 'default',
        'sender': ADMIN_USERNAME,
    }

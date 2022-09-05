import os
import random
from http import HTTPStatus
from typing import Optional

import requests

ADMIN_USERNAME = os.environ['DOLESA_ADMIN_USERNAME']
ADMIN_PASSWORD = os.environ['DOLESA_ADMIN_PASSWORD']
PORT = os.environ.get('PORT', '8080')
HOST = f'http://localhost:{PORT}/dolesa'


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
    my_message = {'text': "sending to default endpoint", 'num': random.randint(1, 1000)}

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
    my_message = {'text': "sending to explicit endpoint", 'num': random.randint(1, 1000)}

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


def test_send_receive__multiple() -> None:
    # first there is nothing to receive
    response_receive_0 = session().post(f'{HOST}/receive')
    assert response_receive_0.status_code == HTTPStatus.OK
    assert response_receive_0.json()['remaining'] == 0
    assert response_receive_0.json()['received'] == []

    # prepare 5 messages
    messages = [{'text': f"my message no {index}"} for index in range(1, 6)]
    assert len(messages) == 5

    # -> send first 2 messages
    response_send_1 = session().post(f'{HOST}/send', json=messages[:2])
    assert response_send_1.status_code == HTTPStatus.ACCEPTED
    assert response_send_1.json() == {'routed': 2}

    # -> send the remaining 3 messages
    response_send_2 = session().post(f'{HOST}/send', json=messages[2:])
    assert response_send_2.status_code == HTTPStatus.ACCEPTED
    assert response_send_2.json() == {'routed': 3}

    # request 1 message -> receive 1
    response_receive_1 = session().post(f'{HOST}/receive')
    assert response_receive_1.status_code == HTTPStatus.OK
    assert response_receive_1.json()['remaining'] == 4
    assert len(response_receive_1.json()['received']) == 1
    assert response_receive_1.json()['received'][0]['message'] == messages[0]

    # request 3 messages -> receive 3
    response_receive_2 = session().post(f'{HOST}/receive', json={'count': 3})
    assert response_receive_2.status_code == HTTPStatus.OK
    assert response_receive_2.json()['remaining'] == 1
    assert len(response_receive_2.json()['received']) == 3
    assert [m['message'] for m in response_receive_2.json()['received']] == messages[1:4]

    # request 2 messages -> receive only 1
    response_receive_3 = session().post(f'{HOST}/receive', json={'count': 2})
    assert response_receive_3.status_code == HTTPStatus.OK
    assert response_receive_3.json()['remaining'] == 0
    assert len(response_receive_3.json()['received']) == 1
    assert response_receive_3.json()['received'][0]['message'] == messages[4]

    # request 1 message -> receive nothing
    response_receive_4 = session().post(f'{HOST}/receive')
    assert response_receive_4.status_code == HTTPStatus.OK
    assert response_receive_4.json()['remaining'] == 0
    assert response_receive_4.json()['received'] == []

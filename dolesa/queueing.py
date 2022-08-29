import json
import logging
import os
from datetime import datetime
from typing import Any

import requests

from dolesa.users import User


logger = logging.getLogger(__name__)

RABBITMQ_USER = os.environ['RABBITMQ_USER']
RABBITMQ_PASS = os.environ['RABBITMQ_PASS']
RABBITMQ_HOST = os.environ['RABBITMQ_HOST']
RABBITMQ_PORT = os.environ['RABBITMQ_PORT']
RABBITMQ_EXCHANGE = os.environ['RABBITMQ_EXCHANGE']
RABBITMQ_TIMEOUT_SECONDS = int(os.environ.get('RABBITMQ_TIMEOUT_SECONDS', 5))


def _load_queues(filename: str = 'queues.txt') -> list[str]:
    with open(filename) as file:
        queues = [line.strip() for line in file]

    if not queues:
        return ['default']

    return queues


QUEUES = _load_queues()
QUEUES_SET = frozenset(QUEUES)
DEFAULT_QUEUE = QUEUES[0]


def send_to_queue(queue: str, *messages: dict[str, Any], sender: User, timestamp: datetime) -> bool:
    return all(_sent_to_queue_single(queue, message, sender, timestamp) for message in messages)


# TODO: use pika instead of HTTP


def _sent_to_queue_single(
    queue: str,
    message: dict[str, Any],
    sender: User,
    timestamp: datetime,
) -> bool:
    if not queue in QUEUES_SET:
        raise KeyError(queue)

    payload = {
        'queue': queue,
        'message': message,
        'sender': sender.username,
        'ts': int(timestamp.timestamp())
    }

    try:
        payload_json = json.dumps(payload, separators=(',', ':'))
    except TypeError as exc:
        raise ValueError(f"failed to encode {message!r}") from exc

    response = requests.post(
        url=f'http://{RABBITMQ_HOST}:{RABBITMQ_PORT}/api/exchanges/%2f/{RABBITMQ_EXCHANGE}/publish',
        auth=(RABBITMQ_USER, RABBITMQ_PASS),
        json={
            'properties': {},
            'routing_key': queue,
            'payload': payload_json,
            'payload_encoding': 'string',
        },
        headers={'Content-Type': 'application/json'},
        timeout=RABBITMQ_TIMEOUT_SECONDS,
    )

    response.raise_for_status()
    return bool(response.json()['routed'])


def receive_from_queue(queue: str, count: int) -> dict[str, Any]:
    if not queue in QUEUES_SET:
        raise KeyError(queue)

    response = requests.post(
        url=f'http://{RABBITMQ_HOST}:{RABBITMQ_PORT}/api/queues/%2f/{queue}/get',
        auth=(RABBITMQ_USER, RABBITMQ_PASS),
        json={
            'count': count,
            'encoding': 'auto',
            'ackmode': 'ack_requeue_false',
        },
        headers={'Content-Type': 'application/json'},
        timeout=RABBITMQ_TIMEOUT_SECONDS,
    )

    response.raise_for_status()
    rabbit_msgs = response.json()
    return {
        'received': [json.loads(rabbit_msg['payload']) for rabbit_msg in rabbit_msgs],
        'remaining': rabbit_msgs[-1]['message_count'] if rabbit_msgs else 0
    }

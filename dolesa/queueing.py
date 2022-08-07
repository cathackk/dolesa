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
RABBITMQ_POST = os.environ['RABBITMQ_PORT']
RABBITMQ_EXCHANGE = os.environ['RABBITMQ_EXCHANGE']
RABBITMQ_QUEUE = os.environ['RABBITMQ_QUEUE']
RABBITMQ_ROUTING_KEY = os.environ['RABBITMQ_ROUTING_KEY']


def send_to_queue(*messages: dict[str, Any], sender: User, ts: datetime) -> bool:
    return all(_sent_to_queue_single(message, sender, ts) for message in messages)


# TODO: use pika instead of HTTP


def _sent_to_queue_single(message: dict[str, Any], sender: User, ts: datetime) -> bool:
    payload = {
        'message': message,
        'sender': sender.username,
        'ts': int(ts.timestamp())
    }

    try:
        payload_json = json.dumps(payload, separators=(',', ':'))
    except TypeError as exc:
        raise ValueError(f"failed to encode {message!r}") from exc

    response = requests.post(
        url=f'http://{RABBITMQ_HOST}:{RABBITMQ_POST}/api/exchanges/%2f/{RABBITMQ_EXCHANGE}/publish',
        auth=(RABBITMQ_USER, RABBITMQ_PASS),
        json={
            'properties': {},
            'routing_key': RABBITMQ_ROUTING_KEY,
            'payload': payload_json,
            'payload_encoding': 'string',
        },
        headers={
            'Content-Type': 'application/json'
        }
    )

    response.raise_for_status()
    return response.json()['routed']


def receive_from_queue(count: int) -> dict[str, Any]:
    response = requests.post(
        url=f'http://{RABBITMQ_HOST}:{RABBITMQ_POST}/api/queues/%2f/{RABBITMQ_QUEUE}/get',
        auth=(RABBITMQ_USER, RABBITMQ_PASS),
        json={
            'count': count,
            'encoding': 'auto',
            'ackmode': 'ack_requeue_false',
        },
        headers={
            'Content-Type': 'application/json'
        }
    )

    response.raise_for_status()
    rabbit_msgs = response.json()
    return {
        'received': [json.loads(rabbit_msg['payload']) for rabbit_msg in rabbit_msgs],
        'remaining': rabbit_msgs[-1]['message_count'] if rabbit_msgs else 0
    }

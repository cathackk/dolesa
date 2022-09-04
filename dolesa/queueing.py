from typing import Any
from typing import Iterator
from typing import Iterable
from typing import Optional

from dataclasses import dataclass

import json
import logging
import os
from datetime import datetime

from jsonschema import validate
import requests
import yaml

from dolesa.users import User


logger = logging.getLogger(__name__)

RABBITMQ_USER = os.environ['RABBITMQ_USER']
RABBITMQ_PASS = os.environ['RABBITMQ_PASS']
RABBITMQ_HOST = os.environ['RABBITMQ_HOST']
RABBITMQ_PORT = os.environ['RABBITMQ_PORT']
RABBITMQ_EXCHANGE = os.environ['RABBITMQ_EXCHANGE']
RABBITMQ_TIMEOUT_SECONDS = int(os.environ.get('RABBITMQ_TIMEOUT_SECONDS', 5))


class Queues:
    def __init__(self, queues: Iterable['Queue']):
        queues_list = list(queues)
        if not queues_list:
            queues_list = [Queue(name='default')]

        self.queues_dict = {q.name: q for q in queues_list}
        self.default_queue = queues_list[0]

    @classmethod
    def load(cls, definition_path: str = 'config/queues.yaml') -> 'Queues':
        with open(definition_path) as file:
            definition = yaml.safe_load(file)
            return cls(
                Queue.from_config_item(item)
                for item in definition['queues']
            )

    def __len__(self) -> int:
        return len(self.queues_dict)

    def __contains__(self, queue_name: str) -> bool:
        return queue_name in self.queues_dict

    def __getitem__(self, queue_name: Optional[str]) -> 'Queue':
        if queue_name is None:
            return self.default_queue

        return self.queues_dict[queue_name]

    def __iter__(self) -> Iterator['Queue']:
        return iter(self.queues_dict.values())


QUEUES = Queues.load()


@dataclass(frozen=True)
class Queue:
    name: str
    json_schema: Optional[dict] = None

    def validate(self, message: dict[str, Any]) -> None:
        if self.json_schema:
            validate(message, self.json_schema)

    @classmethod
    def from_config_item(cls, config_item: dict) -> 'Queue':

        def load_json_schema(filename: Optional[str]) -> Optional[dict]:
            if not filename:
                return None
            path = os.path.join('config', filename)
            with open(path) as file:
                return yaml.safe_load(file)  # type: ignore

        return cls(
            name=config_item['name'],
            json_schema=load_json_schema(config_item.get('schema')),
        )

    def send(
        self,
        *messages: dict[str, Any],
        sender: User,
        timestamp: datetime,
        skip_validation: bool = False
    ) -> bool:
        return all(
            self.send_single(message, sender, timestamp, skip_validation)
            for message in messages
        )

    def send_single(
        self,
        message: dict[str, Any],
        sender: User,
        timestamp: datetime,
        skip_validation: bool = False,
    ) -> bool:
        if not skip_validation:
            self.validate(message)

        payload = {
            'queue': self.name,
            'message': message,
            'sender': sender.username,
            'ts': int(timestamp.timestamp())
        }

        try:
            payload_json = json.dumps(payload, separators=(',', ':'))
        except TypeError as exc:
            raise ValueError(f"failed to encode {message!r}") from exc

        response = requests.post(
            url=self._publish_url,
            auth=(RABBITMQ_USER, RABBITMQ_PASS),
            json={
                'properties': {},
                'routing_key': self.name,
                'payload': payload_json,
                'payload_encoding': 'string',
            },
            headers={'Content-Type': 'application/json'},
            timeout=RABBITMQ_TIMEOUT_SECONDS,
        )

        response.raise_for_status()
        return bool(response.json()['routed'])

    @property
    def _publish_url(self) -> str:
        return (
            f'http://{RABBITMQ_HOST}:{RABBITMQ_PORT}/api/exchanges/%2f/{RABBITMQ_EXCHANGE}/publish'
        )

    def receive(self, count: int) -> dict[str, Any]:
        response = requests.post(
            url=self._get_url,
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

    @property
    def _get_url(self) -> str:
        return f'http://{RABBITMQ_HOST}:{RABBITMQ_PORT}/api/queues/%2f/{self.name}/get'

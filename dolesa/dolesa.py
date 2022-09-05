import logging
import os
from datetime import datetime
from http import HTTPStatus
from typing import Any
from typing import Optional

from flask import Blueprint
from flask import request
from flask_httpauth import HTTPBasicAuth
from jsonschema.exceptions import ValidationError

from dolesa.queues import Queues
from dolesa.users import User
from dolesa.users import authenticate

bp = Blueprint('dolesa', __name__)
auth = HTTPBasicAuth()
logger = logging.getLogger(__name__)

QUEUES = Queues.load()

# TODO: server config
MAX_CONTENT_LENGTH = int(os.environ.get('DOLESA_MAX_CONTENT_LENGTH', 4096))


JSONResponse = tuple[dict[str, Any], int]


@bp.route('/queues', methods=['GET'])
@auth.login_required(role='list')
def queues() -> JSONResponse:
    return {
        'queues': [q.name for q in QUEUES],
        'default_queue': QUEUES.default_queue.name,
    }, HTTPStatus.OK


@bp.route('/info', methods=['GET'])
@bp.route('/queues/<queue_name>', methods=['GET'])
@auth.login_required(role='send')
def queue_info(queue_name: Optional[str] = None) -> JSONResponse:
    try:
        queue = QUEUES[queue_name]
    except KeyError:
        return queue_not_found_response(queue_name)

    return {'queue': queue.name, 'schema': queue.json_schema or {}}, HTTPStatus.OK


@bp.route('/send', methods=['POST'])
@bp.route('/queues/<queue_name>/send', methods=['POST'])
@auth.login_required(role='send')
def send(queue_name: Optional[str] = None) -> JSONResponse:
    try:
        queue = QUEUES[queue_name]
    except KeyError:
        return queue_not_found_response(queue_name)

    # TODO: refactor for readability

    if not request.content_length:
        return {'error': "no data"}, HTTPStatus.BAD_REQUEST
    if request.content_length > MAX_CONTENT_LENGTH:
        return {
            'error': "content too long",
            'description': f"max content length is {MAX_CONTENT_LENGTH}",
        }, HTTPStatus.REQUEST_ENTITY_TOO_LARGE

    request_json = request.get_json(force=True)
    if isinstance(request_json, list):
        try:
            messages = [dict(value) for value in request_json]
        except TypeError:
            return {
                'error': "wrong JSON format",
                'description': "JSON list must contain only objects",
            }, HTTPStatus.UNPROCESSABLE_ENTITY
    elif isinstance(request_json, dict):
        messages = [request_json]
    else:
        return {
            'error': "wrong JSON format",
            'description': "JSON data must be either object or list",
        }, HTTPStatus.UNPROCESSABLE_ENTITY

    try:
        routed = queue.send(
            *messages,
            sender=auth.current_user(),
            timestamp=datetime.now(),
        )

    except ValidationError as exc:
        logger.error("validation failed", exc_info=exc)
        return {
            'error': "invalid message",
            'description': exc.message,
        }, HTTPStatus.UNPROCESSABLE_ENTITY

    except Exception as exc:  # pylint: disable=broad-except
        logger.error("routing failed", exc_info=exc)
        return {'error': "routing failed"}, HTTPStatus.INTERNAL_SERVER_ERROR

    if not routed:
        return {'error': "not routed"}, HTTPStatus.INTERNAL_SERVER_ERROR

    return {"routed": len(messages)}, HTTPStatus.ACCEPTED


@bp.route('/receive', methods=['POST'])
@bp.route('/queues/<queue_name>/receive', methods=['POST'])
@auth.login_required(role='receive')
def receive(queue_name: Optional[str] = None) -> JSONResponse:
    try:
        queue = QUEUES[queue_name]
    except KeyError:
        return queue_not_found_response(queue_name)

    request_json = request.get_json(force=True, silent=True) or {}
    count = request_json.get('count', 1)

    try:
        return queue.receive(count), HTTPStatus.OK

    except Exception as exc:  # pylint: disable=broad-except
        logger.error("failed to receive from queue", exc_info=exc)
        return {'error': "failed to receive from queue"}, HTTPStatus.INTERNAL_SERVER_ERROR


@bp.route('/health')
def health() -> JSONResponse:
    # TODO: check queues as part of health check?
    return {"status": "running"}, HTTPStatus.OK


# TODO: POST /reset


@auth.verify_password
def verify_password(username: str, password: str) -> Optional[User]:
    return authenticate(username, password)


@auth.get_user_roles
def get_user_roles(user: User) -> list[str]:
    return user.permissions


# TODO: raise Exception instead and convert it by Flask into JSON response
def queue_not_found_response(queue_name: Optional[str]) -> JSONResponse:
    return {
        'error': "queue not found",
        'description': f"queue {queue_name!r} is not configured",
    }, HTTPStatus.NOT_FOUND

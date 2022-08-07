import os
from datetime import datetime
from http import HTTPStatus
from typing import Optional

from flask import Flask
from flask import request
from flask_httpauth import HTTPBasicAuth

from dolesa.users import authenticate
from dolesa.users import User
from dolesa.queueing import receive_from_queue
from dolesa.queueing import send_to_queue

app = Flask(__name__)
auth = HTTPBasicAuth()


MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 4096))


@app.route('/send', methods=['POST'])
@auth.login_required(role='publisher')
def send():
    # TODO: refactor for readability
    # TODO: JSON schema validation

    if not request.content_length:
        return "no data given", HTTPStatus.BAD_REQUEST
    if request.content_length > MAX_CONTENT_LENGTH:
        return f"max content length is {MAX_CONTENT_LENGTH}", HTTPStatus.REQUEST_ENTITY_TOO_LARGE

    request_json = request.get_json(force=True)
    if isinstance(request_json, list):
        try:
            messages = [dict(value) for value in request_json]
        except:
            return "JSON list must contain objects only", HTTPStatus.UNPROCESSABLE_ENTITY
    elif isinstance(request_json, dict):
        messages = [request_json]
    else:
        return "JSON must be either dict or list", HTTPStatus.UNPROCESSABLE_ENTITY

    try:
        routed = send_to_queue(*messages, sender=auth.current_user(), ts=datetime.now())
    except Exception as exc:
        app.logger.error("failed to send to queue", exc_info=exc)
        return "failed to send to queue", HTTPStatus.INTERNAL_SERVER_ERROR

    if not routed:
        return "not routed", HTTPStatus.INTERNAL_SERVER_ERROR

    return {"routed": len(messages)}, HTTPStatus.ACCEPTED


@app.route('/receive', methods=['POST'])
@auth.login_required(role='consumer')
def receive():
    request_json = request.get_json(force=True, silent=True) or {}
    count = request_json.get('count', 1)

    try:
        return receive_from_queue(count)
    except Exception as exc:
        app.logger.error("failed to receive from queue", exc_info=exc)
        return "failed to receive from queue", HTTPStatus.INTERNAL_SERVER_ERROR


@app.route('/health')
def health():
    return {"status": "running"}


# TODO: POST /reset


@auth.verify_password
def verify_password(username: str, password: str) -> Optional[str]:
    return authenticate(username, password)


@auth.get_user_roles
def get_user_roles(user: User) -> list[str]:
    return user.roles

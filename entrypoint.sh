#!/bin/sh

set -e

# TODO: move to a config file?
export RABBITMQ_USER=guest
export RABBITMQ_PASS=guest
export RABBITMQ_HOST=localhost
export RABBITMQ_PORT=15672
export RABBITMQ_EXCHANGE=exchange
export RABBITMQ_QUEUE=exchange.q1
export RABBITMQ_ROUTING_KEY=exchange.q1

# start RabbitMQ server
rabbitmq-server -detached

# wait for it to start up
./rabbitmq-init.sh

# run the Flask app
gunicorn --conf ./dolesa/gunicorn_conf.py --bind "0.0.0.0:${PORT:-8080}" dolesa.main:app

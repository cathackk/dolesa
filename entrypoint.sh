#!/bin/sh

set -e

./rabbitmq-init.sh
gunicorn --conf ./dolesa/gunicorn_conf.py --bind 0.0.0.0:80 dolesa.main:app

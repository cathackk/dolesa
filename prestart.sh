#!/bin/sh

# ==> initialize Rabbit MQ <==

# abort on any error
set -e

# abort if any referenced env var is not set
set -u
: "$RABBITMQ_USER"
: "$RABBITMQ_PASS"
: "$RABBITMQ_HOST"
: "$RABBITMQ_PORT"
: "$RABBITMQ_EXCHANGE"
: "$RABBITMQ_QUEUE"
: "$RABBITMQ_ROUTING_KEY"


AUTH="$RABBITMQ_USER:$RABBITMQ_PASS"
API_URL="http://$RABBITMQ_HOST:$RABBITMQ_PORT/api"


# wait for rabbit to go up
./wait-for-it.sh "$RABBITMQ_HOST:$RABBITMQ_PORT"

# create exchange
echo ">>> creating exchange ..."
curl -s -u $AUTH -X PUT "$API_URL/exchanges/%2f/$RABBITMQ_EXCHANGE" \
     -d '{"type":"direct","auto_delete":false,"durable":true,"internal":false,"arguments":{}}'

# create queue
echo ">>> creating queue ..."
curl -s -u $AUTH -X PUT "$API_URL/queues/%2f/$RABBITMQ_QUEUE" \
     -d '{"auto_delete":false,"durable":true,"arguments":{}}'

# creating binding
echo ">>> creating binding ..."
curl -s -u $AUTH -X POST "$API_URL/bindings/%2f/e/$RABBITMQ_EXCHANGE/q/$RABBITMQ_QUEUE" \
     -d '{"routing_key":"'$RABBITMQ_ROUTING_KEY'","arguments":{}}'

# https://hub.docker.com/_/rabbitmq
FROM rabbitmq:3.10-management

# runtime dependencies (Python 3.9 and some other stuff)
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        sudo \
        curl \
        make \
        software-properties-common; \
    sudo add-apt-repository -y ppa:deadsnakes/ppa; \
    sudo apt-get install -y --no-install-recommends python3.9 python3.9-distutils; \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py; \
    python3.9 get-pip.py;

# allow statements and log messages to immediately appear in Knative logs
ENV PYTHONBUFFERED True

# where the app lives
ENV APP_HOME /usr/local/dolesa
WORKDIR $APP_HOME

# install dependencies
COPY requirements.txt .
COPY Makefile .
RUN make install

# copy local support code
COPY wait-for-it.sh rabbitmq-init.sh entrypoint.sh ./
# copy the app
COPY dolesa ./dolesa/
# copy config
COPY users.json queues.txt ./

ENTRYPOINT ["./entrypoint.sh"]

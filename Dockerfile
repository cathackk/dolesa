# https://hub.docker.com/_/rabbitmq
FROM rabbitmq:3.10-management

# runtime dependencies (Python 3.9 and some other stuff)
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        sudo \
        curl \
        jq \
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
RUN pip3.9 install --no-cache-dir --upgrade pip wheel setuptools; \
	pip3.9 install --no-cache-dir --upgrade -r requirements.txt

# copy local support code
COPY scripts ./scripts/
# copy the app
COPY dolesa ./dolesa/
# copy config
COPY config ./config/

ENTRYPOINT ["./scripts/entrypoint.sh"]

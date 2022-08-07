FROM python:3.9

WORKDIR /code

COPY requirements.txt .
COPY Makefile .
RUN make install

COPY wait-for-it.sh .
COPY rabbitmq-init.sh .
COPY entrypoint.sh .
COPY dolesa ./dolesa

ENTRYPOINT ["./entrypoint.sh"]

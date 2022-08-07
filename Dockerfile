FROM tiangolo/uwsgi-nginx-flask:python3.9

WORKDIR /app
COPY Makefile .
COPY requirements.txt .
RUN make install

COPY wait-for-it.sh .
COPY main.py .
COPY prestart.sh .
COPY ./dolesa ./dolesa

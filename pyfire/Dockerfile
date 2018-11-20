FROM python:3.7

RUN pip install kubernetes prometheus_client

COPY ./main.py ./main.py
COPY ./src ./src

COPY ./skyfire ./skyfire

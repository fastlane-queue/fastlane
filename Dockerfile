FROM python:slim

RUN apt update \
    && apt install -y make \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY ./ ./

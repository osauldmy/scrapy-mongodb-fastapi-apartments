FROM python:slim

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt

WORKDIR /app

RUN useradd -m user
USER user

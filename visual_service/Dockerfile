FROM python:3.9-slim

USER root

COPY requirements.txt /tmp/requirements.txt

RUN pip3 install -r /tmp/requirements.txt

WORKDIR /app

CMD ["python3", "main.py"]

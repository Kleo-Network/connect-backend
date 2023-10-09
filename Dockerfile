FROM python:3.11.6

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
COPY . /app
RUN python -m pip install celery
RUN python -m pip install -r /app/requirements.txt
WORKDIR /app

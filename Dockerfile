FROM python:3.13-alpine
LABEL authors="serious-pavel"
LABEL maintainer="serious-pavel"

ENV PYTHONUNBUFFERED=1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
COPY ./app /app
WORKDIR /app
EXPOSE 8000


ARG DEV=false
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client && \
    apk add --update --no-cache --virtual .tmp-build-deps \
      build-base postgresql-dev musl-dev && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true" ] ; \
      then apk add --no-cache chromium chromium-chromedriver && \
      /py/bin/pip install -r /tmp/requirements.dev.txt ; \
    fi && \
    apk del .tmp-build-deps && \
    rm -rf /tmp && \
    if [ "$DEV" = "true" ]; \
      then \
        adduser --disabled-password django-user; \
      else \
        adduser --disabled-password --no-create-home django-user; \
    fi

ENV PATH="/py/bin:$PATH"

USER django-user
FROM python:3.13-alpine
LABEL authors="serious-pavel"
LABEL maintainer="serious-pavel"

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

COPY ./app /app
RUN chmod +x /app/entrypoint.sh

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
    if [ "$DEV" = "true" ]; \
      then \
        adduser --disabled-password django-user; \
      else \
        rm -rf /tmp && \
        adduser --disabled-password --no-create-home django-user; \
    fi

ENV PATH="/py/bin:$PATH"

USER django-user

# Set entrypoint
ENTRYPOINT ["sh", "/app/entrypoint.sh"]

# Default command
CMD ["gunicorn", "app.wsgi:application", "--bind", "0.0.0.0:8000"]
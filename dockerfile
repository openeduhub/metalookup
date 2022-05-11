FROM python:3.9-alpine

RUN adduser -D extractor

WORKDIR /home/extractor

RUN apk add --update --no-cache --virtual .build-deps g++ python3-dev libxml2 libxml2-dev libffi-dev openssl-dev
RUN apk add libxslt-dev curl

# Needed for psycopg2
RUN apk update && \
    apk add --virtual build-deps gcc musl-dev && \
    apk add postgresql-dev

# make wheel file built with poetry build available in docker build step
COPY ./*.whl /home/extractor
# install the wheel file and all its (transitive) dependencies
RUN pip install --no-cache-dir /home/extractor/*.whl
RUN apk del .build-deps

USER extractor

# execute the entrypoint defined in pyproject.toml
CMD meta-lookup

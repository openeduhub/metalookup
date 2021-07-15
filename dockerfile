FROM python:3.9-alpine

RUN adduser -D extractor

WORKDIR /home/extractor

RUN apk add --update --no-cache --virtual .build-deps g++ python3-dev libxml2 libxml2-dev libffi-dev openssl-dev
RUN apk add libxslt-dev curl

# Needed for psycopg2
# RUN curl -o libpq.deb -fSL "http://apt.postgresql.org/pub/repos/apt/pool/main/p/postgresql-13/libpq-dev_13.3-1.pgdg20.04+1_amd64.deb"
# RUN apk add dpkg
# RUN dpkg -i libpq.deb
RUN apk update && \
    apk add --virtual build-deps gcc musl-dev && \
    apk add postgresql-dev

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN apk del .build-deps

# First copy the data, then give ownership to it, then switch to correct user
COPY src/ .

RUN chown -R extractor:extractor ./

USER extractor

CMD python manager.py
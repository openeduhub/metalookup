FROM python:3.9-alpine

RUN adduser -D extractor

WORKDIR /home/extractor

RUN apk add --update --no-cache --virtual .build-deps g++ python3-dev libxml2 libxml2-dev libffi-dev openssl-dev
RUN apk add libxslt-dev curl

# Needed for psycopg2
RUN apk update && \
    apk add --virtual build-deps gcc musl-dev && \
    apk add postgresql-dev

# Needed for re2
RUN apk add python3-dev
RUN apk add build-base # https://github.com/gliderlabs/docker-alpine/issues/24
RUN apk add --update git
RUN git clone https://code.googlesource.com/re2
WORKDIR /home/extractor/re2
RUN make
RUN make test
RUN make install
RUN make testinstall
RUN apk add cmake
WORKDIR /home/extractor

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN apk del .build-deps
RUN apk del build-deps

# First copy the data, then give ownership to it, then switch to correct user
COPY src/ .

RUN chown -R extractor:extractor ./

USER extractor

CMD python manager.py

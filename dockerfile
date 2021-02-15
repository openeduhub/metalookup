FROM python:3.9-alpine

RUN adduser -D extractor

WORKDIR /home/extractor

RUN apk add --update --no-cache --virtual .build-deps g++ python3-dev libxml2 libxml2-dev libffi-dev openssl-dev
RUN apk add libxslt-dev curl

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN apk del .build-deps

# First copy the data, then give ownership to it, then switch to correct user
COPY src/ .

RUN chown -R extractor:extractor ./

USER extractor

CMD python manager.py
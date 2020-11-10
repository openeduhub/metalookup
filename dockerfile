FROM python:3.9-alpine

RUN adduser -D extractor

WORKDIR /home/extractor

RUN apk add --update --no-cache --virtual .build-deps g++ python3-dev libxml2 libxml2-dev
RUN apk add libxslt-dev

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN apk del .build-deps

COPY src/ .

RUN chown -R extractor:extractor ./

USER extractor

CMD python manager.py
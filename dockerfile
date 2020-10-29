FROM python:3.9-alpine

RUN adduser -D extractor

WORKDIR /home/extractor

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY src/app/api.py ./

RUN chown -R extractor:extractor ./

USER extractor

CMD uvicorn api:app --host 0.0.0.0 --port 5057
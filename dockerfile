FROM python:3.9-alpine

RUN adduser -D extractor

WORKDIR /home/extractor

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY src/app/api.py ./app/api.py
COPY src/app/communication.py ./app/communication.py
COPY src/manager.py ./

RUN chown -R extractor:extractor ./

USER extractor

CMD python manager.py
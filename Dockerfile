FROM python:slim

COPY ./requirements.txt ./
RUN pip install -r requirements.txt

COPY ./ ./

CMD uvicorn main:app --host 0.0.0.0

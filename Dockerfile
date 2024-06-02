FROM python:3.10

RUN mkdir /code
WORKDIR /code

COPY requirements.txt /code/requirements.txt
COPY deeplx.py /code/deeplx.py
COPY main.py /code/main.py
COPY proxy.py /code/proxy.py

RUN pip install -r /code/requirements.txt

ENV PROXY_FILE=/data/proxy.txt

EXPOSE 1188

ENTRYPOINT ["uvicorn", "main:app", "--host=0.0.0.0", "--port=1188"]

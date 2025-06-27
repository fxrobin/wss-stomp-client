FROM python:3.14.0b3-alpine3.21

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT [ "python", "./wss-stomp-client.py" ]

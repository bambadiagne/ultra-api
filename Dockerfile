FROM python:3.9-slim

WORKDIR /backend

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt
EXPOSE 5000
COPY . .
RUN chmod +x start.sh
ENTRYPOINT ["/bin/sh", "-c", "/backend/start.sh"]
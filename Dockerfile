FROM python:3.9-slim

WORKDIR /backend

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
EXPOSE 5000
COPY . .

CMD [ "python3", "app.py"]
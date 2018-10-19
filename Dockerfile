FROM python:3.7-slim

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY exporter.py ./
EXPOSE 3000

CMD [ "python", "./exporter.py"]

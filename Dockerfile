FROM python:3.7-slim

WORKDIR /usr/src/app
ADD requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
ADD exporter.py ./
EXPOSE 3000

CMD [ "python", "./exporter.py"]

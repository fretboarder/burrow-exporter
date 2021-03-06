FROM python:3.7-slim

WORKDIR /usr/src/app
ADD requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd -M lagexport
ADD *.py ./
EXPOSE 3000

USER lagexport

CMD [ "python", "./exporter.py"]

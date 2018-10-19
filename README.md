# Simple Prometheus metrics exporter for Burrow

## Kafka consumer lag monitoring made easy

This tiny little tool aims to be the missing link between Burrow and Prometheus for exposing Kafka consumer lags.

Written in Python. From Austria. 

## Environment settings

### BURROW_POLLING_INTERVAL (default = 5 seconds)
### METRICS_PORT (default = 3000)
### BURROW_HOST (default = "localhost")
### BURROW_PORT (default = 8000)

## Docker

### Use pre-build imaged from Quay

    $ docker run -d -p 3000:3000 quay.io/fretboarder/burrow-exporter

### ... or build it by yourself

    $ docker build -t burrow-exporter .
    $ docker run -d -p 3000:3000 burrow-exporter

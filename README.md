# Simple Prometheus metrics exporter for Burrow and Remora

## Kafka consumer lag monitoring made easy

This tiny little tool exports Kafka consumer lags as Prometheus metrics from 
[Remora](https://github.com/zalando-incubator/remora) as well as from 
[Burrow](https://github.com/linkedin/Burrow).

Written in Python. From Austria. 

## Environment settings

### LAG_POLLING_INTERVAL (default = 5 seconds)
### LAG_BACKEND_TYPE (default = burrow)
* remora
* burrow
### METRICS_PORT (default = 3000)
The port where promethes metrics will be exposed
### LOG_LEVEL (default = INFO)
* debug
* info
* warning
* error
* critical
### ADD_ENV_LABELS (default = "")
Additional labels from the environment that shall be attached to each metric, colon separated.
### BURROW_HOST (default = "localhost")
The hostname (or IP address) where Burrow is listening
### BURROW_PORT (default = 8000)
The port where Burrow is listening
### REMORA_HOST (default = "localhost")
The hostname (or IP address where Remora is listening)
### REMORA_PORT (default = 8000)
The port where Remora is listening

Colon-separated list of environment variables that shall be used as labels on a metric

## Docker

The latest version is available via quay.io/fretboarder/kafka-lag-exporter

### Use pre-build imaged from Quay

    $ docker run -d -p 3000:3000 quay.io/fretboarder/kafka-lag-exporter

### ... or build it by yourself

    $ docker build -t kafka-lag-exporter .
    $ docker run -d -p 3000:3000 kafka-lag-exporter

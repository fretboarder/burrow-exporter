import time, os
import json,urllib.request, http.client
import prometheus_client as pc
import logging

PROGRAM = "burrow-exporter"

BURROW_POLLING_INTERVAL = os.getenv('POLLING_INTERVAL', default=5)
METRICS_PORT = int(os.getenv("METRICS_PORT", default=3000))
BURROW_HOST = os.getenv("BURROW_HOST", default="localhost")
BURROW_PORT = int(os.getenv("BURROW_PORT", default=8000))
BURROW_ENDPOINT = F"http://{BURROW_HOST}:{BURROW_PORT}"
ENV_LABELS = os.getenv("ADD_ENV_LABELS", default="")

logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(message)s', level=logging.INFO)
def log(s):
    logging.info('{}'.format(s))

def url_loader(get_path):
    """ loads a JSON document from an endpoint """
    def wrapper(*args, **kwargs):
        path,transform,key = get_path(*args, **kwargs)
        try:
            resp = urllib.request.urlopen(F"{BURROW_ENDPOINT}/{path}")
            body = json.loads(resp.read())
            return transform(body[key])
        except Exception as ex:
            log("Exception: {}".format(ex))
            log(F"{BURROW_ENDPOINT}/{path}")
            return []
    return wrapper

@url_loader
def topics(cluster, consumer):
    topic_transform = lambda body: [ { 'topicName' : k, 'stats': body[k] } for k in body ]
    return (F"v3/kafka/{cluster}/consumer/{consumer}", topic_transform, "topics")

@url_loader
def consumers(cluster):
    return (F"v3/kafka/{cluster}/consumer", lambda id: id, "consumers")

@url_loader
def clusters():
    return (F"v3/kafka", lambda id: id, "clusters")

def jdump(o):
    for l in json.dumps(o, indent=2).split('\n'):
        log(l)

def map_env_labels(labels):
    return [ os.getenv(l) for l in labels.split(":") if len(l) ]

def append_labels(l1, l2):
    return l1 + [l for l in l2 if len(l)]

metrics = {}
def init_prometheus():
    metric_labels = ['cluster','consumer','topic'] + [ l for l in ENV_LABELS.split(":") if len(l) ]
    log(F"labels: {metric_labels}")
    metrics['lags'] = pc.Gauge('kafka_consumer_current_lag', 'Kafka Consumer Lag', metric_labels)
    pc.start_http_server(METRICS_PORT)

def update_metrics(metrics_dict, sep):
    for m in metrics_dict:
        labels = m.split(sep) + map_env_labels(ENV_LABELS)
        metrics['lags'].labels(*labels).set(metrics_dict[m])

def request_lags():
    consumer_info = [ { 'clusterName': cluster, 'consumers' : 
                        [ 
                            { 'consumerName': cons,
                            'topics': [ t for t in topics(cluster, cons) ]
                            } for cons in consumers(cluster)
                        ]
                        } for cluster in clusters()
                    ]

    metric_string_dict = {
        F"{i['clusterName']}@{c['consumerName']}@{t['topicName']}" : int(s['current-lag'])
            for i in consumer_info
            for c in i['consumers']
            for t in c['topics']
            for s in t['stats']
    }

    # jdump(metric_string_dict)
    update_metrics(metric_string_dict, '@')

if __name__ == "__main__":        
    log(F"===== Starting {PROGRAM} =====")
    log(F"== metrics available on port {METRICS_PORT}")
    log(F"== polling interval {BURROW_POLLING_INTERVAL} seconds")
    log(F"== Burrow endpoint {BURROW_ENDPOINT}")
    init_prometheus()
    try:
        while True:
            request_lags()
            time.sleep(BURROW_POLLING_INTERVAL)
    except KeyboardInterrupt as kb:
        log("Interrupted.")
    except Exception as ex:
        log("Unexpected exception {}".format(ex))
    else:
        pass
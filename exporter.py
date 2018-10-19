import asyncio, os
import json,urllib.request, http.client
import prometheus_client as pc

PROGRAM = "burrow-exporter"

BURROW_POLLING_INTERVAL = os.getenv('POLLING_INTERVAL', default=5)
METRICS_PORT = os.getenv("METRICS_PORT", default=3000)
BURROW_HOST = os.getenv("BURROW_HOST", default="localhost")
BURROW_PORT = os.getenv("BURROW_PORT", default=8000)
BURROW_ENDPOINT = F"http://{BURROW_HOST}:{BURROW_PORT}"

def log(*args):
    print(F"{PROGRAM}:", *args)

def url_loader(get_path):
    """ loads a JSON document from an endpoint """
    def wrapper(*args, **kwargs):
        path,transform,key = get_path(*args, **kwargs)
        try:
            resp = urllib.request.urlopen(F"{BURROW_ENDPOINT}/{path}")
            body = json.loads(resp.read())
            return transform(body[key])
        except Exception as ex:
            log(F"Exception: ", ex)
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
    print(json.dumps(o, indent=2))

async def request_lags():
    metric_labels = ['cluster','consumer','topic']
    lag_metric = pc.Gauge('kafka_consumer_current_lag', 'Kafka Consumer Lag', metric_labels)
    while True:
        consumer_info = [ { 'clusterName': cluster, 'consumers' : 
                            [ 
                              { 'consumerName': cons,
                                'topics': [ t for t in topics(cluster, cons) ]
                              } for cons in consumers(cluster)
                            ]
                          } for cluster in clusters()
                        ]

        lagdict = {
            F"{i['clusterName']}@{c['consumerName']}@{t['topicName']}" : int(s['current-lag'])
                for i in consumer_info
                for c in i['consumers']
                for t in c['topics']
                for s in t['stats']
        }

        for m in lagdict:
            cluster,consumer,topic = m.split('@')
            lag_metric.labels(cluster=cluster,consumer=consumer,topic=topic).set(lagdict[m])

        await asyncio.sleep(BURROW_POLLING_INTERVAL)
        
async def main():
    log(F"===== Starting {PROGRAM} =====")
    log(F"== metrics available on port {METRICS_PORT}")
    log(F"== polling interval {BURROW_POLLING_INTERVAL} seconds")
    log(F"== Burrow endpoint {BURROW_ENDPOINT}")
    poller = asyncio.create_task(request_lags())
    pc.start_http_server(METRICS_PORT)
    await poller
    
asyncio.run(main(), debug=False)
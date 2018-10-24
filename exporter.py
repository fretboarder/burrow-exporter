import time, os
import json,urllib.request, http.client
import prometheus_client as pc
from log import *

##############################
env = {}
def init_environment():
    """ Initializes the environment """
    env_vars = [
        ( "LAG_POLLING_INTERVAL", 5 ),
        ( "LAG_BACKEND_TYPE", "remora" ),
        ( "METRICS_PORT", 3000 ),
        ( "LOG_LEVEL", "INFO" ),
        ( "ADD_ENV_LABELS", ""),
        ( "BURROW_HOST", "localhost"),
        ( "BURROW_PORT", 8000),
        ( "REMORA_HOST", "localhost"),
        ( "REMORA_PORT", 9000)
    ]
    for e in env_vars:
        env[e[0]] = os.getenv(e[0], e[1])

    env['LAG_ENDPOINT'] =  F"http://{env['REMORA_HOST']}:{env['REMORA_PORT']}" if env['LAG_BACKEND_TYPE'] == "remora" \
                      else F"http://{env['BURROW_HOST']}:{env['BURROW_PORT']}"

##############################
def dump_env():
    """ Dumps the environment settings """
    for e in env: 
        logI("- {} = {}".format(e, env[e]))

###############################
def url_loader(get_path):
    """ loads a JSON document from an endpoint """
    def wrapper(*args, **kwargs):
        path,transform,key = get_path(*args, **kwargs)
        try:
            resp = urllib.request.urlopen(F"{env['LAG_ENDPOINT']}/{path}")
            body = json.loads(resp.read())
            return transform(body[key]) if key != None else transform(body)
        except Exception as ex:
            logI("Exception: {}".format(ex))
            logI(F"{env['LAG_ENDPOINT']}/{path}")
            return []
    return wrapper

##############################
@url_loader
def burrow_topics(cluster, consumer):
    topic_transform = lambda topics: [ { 
        'topicName' : t, 
        'stats': [{ 
            'partition': i, 
            'current-lag': topics[t][i]['current-lag'] 
             } for i in range(len(topics[t]))] 
        } for t in topics ]
    return (F"v3/kafka/{cluster}/consumer/{consumer}", topic_transform, "topics")

##############################
@url_loader
def burrow_consumers(cluster):
    return (F"v3/kafka/{cluster}/consumer", lambda id: id, "consumers")

##############################
@url_loader
def burrow_clusters():
    return (F"v3/kafka", lambda id: id, "clusters")

##############################
def remora_clusters():
    return [ "local" ]

##############################
@url_loader
def remora_consumers(cluster=None):
    return ("consumers", lambda id: id, None)

##############################
@url_loader
def remora_topics(cluster, consumer):
    topic_transform = lambda assignment: [ { 'topicName' : pa['topic'], 'stats': [{'partition':pa['partition'], 'current-lag': pa['lag']}] }  for pa in assignment ]
    return (F"consumers/{consumer}", topic_transform, 'partition_assignment')

topics = lambda cl,co: remora_topics(cl,co) if env['LAG_BACKEND_TYPE'] == "remora" else burrow_topics(cl,co)
consumers = lambda c: remora_consumers(c) if env['LAG_BACKEND_TYPE'] == "remora" else burrow_consumers(c)
clusters = lambda: remora_clusters() if env['LAG_BACKEND_TYPE'] == "remora" else burrow_clusters()

##############################
def map_env_labels(labels):
    return [ os.getenv(l) for l in labels.split(":") if len(l) ]

##############################
metrics = {}
def init_prometheus():
    """ Initializes prometheus """
    metric_labels = ['cluster','consumer','topic','partition'] + [ l for l in env['ADD_ENV_LABELS'].split(":") if len(l) ]
    logI(F"labels: {metric_labels}")
    metrics['lags'] = pc.Gauge('kafka_consumer_lag', 'Kafka Consumer Lag', metric_labels)
    pc.start_http_server(int(env['METRICS_PORT']))

##############################
def update_metrics(metrics_dict, sep):
    """ Update the prometheus metrics with the latest values """
    for m in metrics_dict:
        labels = m.split(sep) + map_env_labels(env['ADD_ENV_LABELS'])
        metrics['lags'].labels(*labels).set(metrics_dict[m])

##############################
def get_lags():
    # This comprehension generates a compound JSON document from
    # various REST calls
    consumer_info = [ { 'clusterName': cluster, 'consumers' : 
                        [ 
                            { 'consumerName': cons,
                            'topics': [ t for t in topics(cluster, cons) ]
                            } for cons in consumers(cluster)
                        ]
                      } for cluster in clusters()
                    ]
    return consumer_info

##############################
def request_lags():
    """ Get the consumer lags from the Lag providing endpoint """
    consumer_info = get_lags()
    jdump(consumer_info)
    
    # Create a dictionary of metric names as keys and current lags as values
    metric_string_dict = {
        F"{i['clusterName']}@{c['consumerName']}@{t['topicName']}@{s['partition']}" : int(s['current-lag'])
            for i in consumer_info
            for c in i['consumers']
            for t in c['topics']
            for s in t['stats']
    }
    jdump(metric_string_dict)

    update_metrics(metric_string_dict, '@')

##############################
# Main
##############################
if __name__ == "__main__":        
    dump_env()
    try:
        init_environment()
        init_logging(env['LOG_LEVEL'])
        init_prometheus()
        while True:
            request_lags()
            time.sleep(int(env['LAG_POLLING_INTERVAL']))
    except KeyboardInterrupt as kb:
        logI("Interrupted.")
    except Exception as ex:
        logW("Unexpected exception {}".format(ex))
    else:
        pass
        
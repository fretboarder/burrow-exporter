#!/usr/bin/env python3

from kafka import KafkaProducer
import os, time, random, json

env_vars = [
    ('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
]

env={}
for e in env_vars:
    env[e[0]] = os.getenv(e[0], e[1])

ks = lambda key: str(key).encode()

def vs(key):
    return json.dumps(key).encode()
    


producer = KafkaProducer(
    bootstrap_servers=env['KAFKA_BOOTSTRAP_SERVERS'], acks='all',
    key_serializer=ks,
    value_serializer=vs
    )
for s in (i for i in range(5000)):
    t = int(10 * random.random()) % 3 + 1
    j = { 'key': s, 'value': 'This is message {:09d}'.format(s) }
    producer.send(F"test-topic{t}", value=j, key=t)
    
time.sleep(2)
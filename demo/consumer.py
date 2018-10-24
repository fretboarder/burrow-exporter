#!/usr/bin/env python3

from kafka import KafkaConsumer
import os, time, json

env_vars = [
    ('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
    ('KAFKA_CONSUMER_GROUP', 'test-topic-consumer')
]

env={}
for e in env_vars:
    env[e[0]] = os.getenv(e[0], e[1])

consumer = KafkaConsumer(bootstrap_servers=env['KAFKA_BOOTSTRAP_SERVERS'], group_id=env['KAFKA_CONSUMER_GROUP'])
consumer.subscribe(pattern='test-topic*')
for msg in consumer:
    key = msg.key.decode()
    val = json.loads(msg.value.decode())
    print(F"{msg.topic}: key= {key} value= {val}")

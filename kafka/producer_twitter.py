import tweepy
import time
from kafka import KafkaProducer
import json
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
bearer_token = os.getenv("TWITTER_BEARER_TOKEN")

client = tweepy.Client(bearer_token=bearer_token)

producer = KafkaProducer(
    bootstrap_servers='localhost:9092', # kafka:9092
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

topic = 'tweets-eventos-sismiscos'

query = '''
(temblor OR sismo OR terremoto OR "movimiento sísmico" OR 
 huaico OR desborde OR alud OR 
 "lluvia fuerte" OR lloviendo OR inundación OR inundado OR 
 "viento fuerte" OR vendaval OR 
 emergencia OR alerta OR evacuación OR pánico)
(Lima OR Perú OR Callao)
-is:retweet -is:reply lang:es
'''


since_id = None
max_results = 25 # usualmente 25 o 50

response = client.search_recent_tweets(
    query=query,
    tweet_fields=['created_at', 'author_id', 'lang'],
    max_results=max_results,
    since_id=since_id
)

print(response.meta)

if response.data:
    for tweet in response.data:
        data = {
            "id": tweet.id,
            "usuario": tweet.author_id,
            "texto": tweet.text,
            "fecha": str(tweet.created_at),
        }
        print(f"Enviando: {data}")
        producer.send(topic, data)
    since_id = response.data[0].id


# ==== Finalizar Kafka correctamente ====
producer.flush()
producer.close()
print("✅ Envío a Kafka completado correctamente.")
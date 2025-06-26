from kafka import KafkaConsumer
import json
from pymongo import MongoClient

# Conecta a MongoDB
cliente_mongo = MongoClient('mongodb://localhost:27017')
db = cliente_mongo["tweets"]
coleccion = db["sismos"]

# Asegura índice único por tweet ID (una vez basta crear esto
coleccion.create_index("id", unique=True)

# Inicializa el consumer
consumer = KafkaConsumer(
    'tweets-eventos-sismiscos',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='grupo-sismos',
    value_deserializer=lambda v: json.loads(v.decode('utf-8')),
    consumer_timeout_ms=30000  # <== termina después de 30s sin nuevos mensajes
)

print("Consumidor activo...\n")

max_mensajes = 100
contador = 0

for mensaje in consumer:
    tweet = mensaje.value
    tweet['procesado'] = False

    try:
        coleccion.insert_one(tweet)
        print(f"✅ Guardado: {tweet['usuario']} ({tweet['fecha']})")
        contador += 1
    except Exception as e:
        print(f"⚠️  No insertado (duplicado): {e}")

    if contador >= max_mensajes:
        break

consumer.close()
print(f"\n🔚 Proceso finalizado. Se guardaron {contador} tweets.")
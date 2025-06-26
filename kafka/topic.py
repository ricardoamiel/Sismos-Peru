from confluent_kafka.admin import AdminClient, NewTopic

# Configura conexión al broker de Kafka
admin_client = AdminClient({
    "bootstrap.servers": "localhost:9092"
})

# Define el nuevo tópico
topic_name = "tweets-eventos-sismiscos"
nuevo_topico = NewTopic(topic=topic_name, num_partitions=1, replication_factor=1)

# Intenta crearlo
try:
    response = admin_client.create_topics([nuevo_topico])
    future = response[topic_name]
    future.result()  # Espera a que se cree o lance error
    print(f"Tópico '{topic_name}' creado con éxito.")
except Exception as e:
    print(f"No se pudo crear el tópico: {e}")

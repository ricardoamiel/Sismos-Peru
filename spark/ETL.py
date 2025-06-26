from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lower, regexp_replace, trim, when
from pymongo import MongoClient
from bson.objectid import ObjectId

# Crear sesión de Spark con el conector MongoDB
spark = SparkSession.builder \
    .appName("ETL_Tweets_Sismos") \
    .master("local[*]") \
    .config("spark.jars.packages", "org.mongodb.spark:mongo-spark-connector_2.12:10.5.0,""org.mongodb:mongodb-driver-sync:4.10.2") \
    .config("spark.mongodb.read.connection.uri", "mongodb://localhost:27017/tweets.sismos") \
    .config("spark.mongodb.write.connection.uri", "mongodb://localhost:27017/tweets.tweets_procesados") \
    .getOrCreate()

# Leer solo los documentos no procesados
df_raw = spark.read.format("mongodb").load()
df_nuevos = df_raw.filter(col("procesado") == False)

def procesar_tweets(df):
    df = df.withColumn("texto_limpio", col("texto"))
    df = df.withColumn("texto_limpio", regexp_replace("texto_limpio", r"http\S+", ""))
    df = df.withColumn("texto_limpio", regexp_replace("texto_limpio", r"@\w+", ""))
    df = df.withColumn("texto_limpio", regexp_replace("texto_limpio", r"#", ""))
    df = df.withColumn("texto_limpio", regexp_replace("texto_limpio", r"[^\w\s\u00C0-\u017F\u1E00-\u1EFF\u2600-\u27BF]", ""))
    df = df.withColumn("texto_limpio", lower(col("texto_limpio")))
    df = df.withColumn("texto_limpio", regexp_replace("texto_limpio", r"\s+", " "))
    df = df.withColumn("texto_limpio", trim(col("texto_limpio")))

    patrones = r"(sismo|temblor|terremoto|huaico|alud|desborde|lluvia fuerte|inundaci[oó]n|vendaval|viento fuerte|emergencia|alerta|evacuaci[oó]n|p[aá]nico)"
    df = df.withColumn("evento_detectado", when(col("texto_limpio").rlike(patrones), "Sí").otherwise("No"))

    return df

# Procesar
if df_nuevos.count() > 0:
    tweets_procesados = procesar_tweets(df_nuevos)

    # Guardar resultado
    tweets_procesados.write.format("mongodb").mode("append").save()

    # Marcar como procesados en MongoDB
    ids_procesados = df_nuevos.select("_id").rdd.map(lambda row: row["_id"]).collect()

    mongo = MongoClient("mongodb://localhost:27017")
    col = mongo["tweets"]["sismos"]
    for _id in ids_procesados:
        if isinstance(_id, str):
            _id = ObjectId(_id)
        col.update_one({"_id": _id}, {"$set": {"procesado": True}})

spark.stop()

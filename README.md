# Análisis de Eventos Sísmicos a partir de Tweets en Perú

## 1. Introducción y Justificación

Perú es una región altamente sísmica, y la detección temprana y análisis de la percepción ciudadana sobre eventos sísmicos puede ayudar a mejorar la respuesta de emergencia y la concientización pública. Este proyecto propone un sistema de scraping en streaming de tweets relacionados a sismos y alertas, que procesa, resume y visualiza información relevante para usuarios y autoridades mediante dashboards interactivos y modelos de lenguaje.

## 2. Descripción del Dataset

* **Origen:** Tweets públicos de Twitter con palabras clave relacionadas a sismos, temblores, huaicos, inundaciones, emergencias y evacuaciones en Perú.
* **Volumen aproximado:** \~50–100 tweets por ciclo de scraping (configurable en Kafka/`max_results`).
* **Estructura:**

  * `id`: Identificador único del tweet
  * `usuario`: ID de autor
  * `texto`: Contenido original
  * `fecha`: Fecha y hora de publicación
  * `texto_limpio`: Texto procesado
  * `evento_detectado`: Señal de mención de evento sísmico

## 3. Dificultad Técnica

* Integración y orquestación en tiempo real con **Kafka**, **Airflow** y **Spark**.
* Conectores y sincronización entre **MongoDB** y Spark vía `mongo-spark-connector`.
* Limpieza y normalización de texto con expresiones regulares y NLP básico.
* Generación de insights estructurados con **LLMs** (`dolphin-llama3:8b`) y prompt engineering.
* Visualización interactiva con **Streamlit** y **Folium**.

## 4. Herramientas y Tecnologías Empleadas

* **Python** (v3.8+)
* **Kafka** (Producer/Consumer con `tweepy` y `confluent_kafka`)
* **MongoDB** (almacenamiento de crudo y procesado)
* **Apache Spark** (ETL batch streaming)
* **Airflow** (orquestación y scheduling)
* **LLMs** via Ollama (`dolphin-llama3:8b`)
* **Streamlit** y **streamlit-folium**
* **Folium** (mapas)
* **NLTK** (stopwords)
* **Matplotlib** (gráficos de barras horizontales)

## 5. Instrucciones para Ejecución

1. Clonar el repositorio:

   ```bash
   [git clone https://github.com/usuario/proyecto-sismos-tweets.git](https://github.com/ricardoamiel/Sismos-Peru.git)
   cd proyecto-sismos-tweets
   ```
2. Configurar variables de entorno:

   ```bash
   export X_TOKEN=<TWITTER_BEARER_TOKEN>
   export MONGO_URI="mongodb://localhost:27017"
   ```
3. Iniciar servicios:

   * MongoDB
   * Kafka (zookeeper + broker)
   * Airflow Scheduler y Webserver
4. Crear tópico en Kafka (opcional si ya existe):

   ```bash
   python kafka_admin.py
   ```
5. Ejecutar DAG de scraping en Airflow o manualmente:

   ```bash
   airflow dags trigger scraping_sismos
   ```
6. Lanzar procesamiento Spark:

   ```bash
   python etl_sparksismos.py
   ```
7. Iniciar dashboard:

   ```bash
   streamlit run dashboard_sismos.py
   ```

## 6. Arquitectura del Proyecto

**Descripción:**

1. **Scraping de Twitter**: `tweepy` busca tweets en streaming con palabras clave.
2. **Producer Kafka**: Publica tweets al topic `tweets-eventos-sismiscos`.
3. **Consumer Kafka → MongoDB**: Inserta los mensajes sin procesar en `tweets.sismos`.
4. **ETL con Spark**: Lee documentos no procesados, limpia texto, detecta eventos y escribe en `tweets.tweets_procesados`. Luego marca originales como procesados.
5. **Batch Airflow**: Orquesta el pipeline completo (scraping, ETL) en horarios programados.
6. **Insights con LLM**: Lee últimos tweets procesados, utiliza prompt engineering en `dolphin-llama3:8b` para generar resúmenes, emociones, daños, etiquetas y preguntas frecuentes. Guarda resultados en `tweets.resumenes`.
7. **Dashboard Streamlit**: Consume `resumenes` y `tweets_procesados`, despliega:

   * Resumen general e insights con emojis y mapas.
   * Gráficos de acumulación temporal, horas, palabras frecuentes y geolocalización.

## 7. Descripción del Proceso ETL/ELT

* **Extract:** Lectura directa de MongoDB (`tweets.sismos`) con conector Spark.
* **Transform:**

  * Eliminación de URLs, mentions y caracteres especiales.
  * Normalización a minúsculas y trimming.
  * Detección de patrones de evento con expresiones regulares.
* **Load:** Escritura de datos enriquecidos en MongoDB (`tweets_procesados`) y actualización de estado de los originales.

## 8. Resultados Obtenidos y Análisis

* **Insights Estructurados:** Contexto y tono emocional de eventos, daños reportados y alertas comunes.
* **Dashboard Interactivo:** Permite navegar por resúmenes históricos, analizar acumulación y frecuencia temporal, visualizar zonas afectadas en mapa.
* **Valor:** Información consolidada de percepción ciudadana para toma de decisiones en emergencias.

## 9. Dificultades Identificadas

* Límite de tasa de la API de Twitter y manejo de `since_id`.
* Parsing robusto de texto con diversidad de formatos y tildes.
* Sincronización y consistencia entre Spark y MongoDB.
* Prompt engineering para obtener salidas estructuradas del LLM.

## 10. Conclusiones y Posibles Mejoras

* **Conclusiones:** El pipeline completo demuestra la viabilidad de integrar datos sociales en tiempo real con procesamiento masivo y LLMs para análisis de crisis.
* **Mejoras:**

  * Añadir geolocalización más precisa (coordenadas) en Tweets.
  * Escalar el ETL a cluster Spark y Kafka multi-partitions.
  * Integrar otras fuentes (RSS, alertas oficiales).
  * Implementar notificaciones push ante eventos críticos.

---

*Proyecto desarrollado por Josué Poma*

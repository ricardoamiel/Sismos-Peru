***
![logo](https://github.com/user-attachments/assets/71623834-8d22-476d-9208-2ed2f0bbfbb8)


# Proyecto: Análisis de Sismos en Perú mediante Scraping y LLMs

## Introducción y justificación del problema a resolver

Perú es un país ubicado en el Cinturón de Fuego del Pacífico, una de las zonas con mayor actividad sísmica del mundo. La monitorización y análisis de estos eventos en tiempo real es crucial para la gestión de desastres, la rápida difusión de información y la comprensión del impacto social. Las redes sociales, especialmente Twitter (ahora X), se han convertido en una fuente de información ciudadana inmediata, donde los usuarios reportan eventos casi al instante. Sin embargo, esta información es masiva, no estructurada, ruidosa y contiene desde reportes verídicos hasta pánico y desinformación. Este proyecto aborda el desafío de capturar, procesar y analizar esta corriente de datos en tiempo real para extraer insights valiosos. El objetivo es construir un sistema automatizado que:

1.  **Capture** tweets relevantes sobre sismos y otros eventos en Perú.
2.  **Procese y limpie** los datos para hacerlos analizables.
3.  **Utilice un Modelo de Lenguaje Grande (LLM)** para resumir la situación, detectar emociones, identificar zonas afectadas y extraer información clave.
4.  **Visualice** estos insights en un dashboard interactivo para facilitar la toma de decisiones y el entendimiento público.

## Arquitectura del proyecto

La solución se basa en una arquitectura de procesamiento de datos en streaming y por lotes, que integra diversas tecnologías para cubrir el ciclo de vida completo del dato, desde su ingesta hasta su visualización.

### Diagrama de la Arquitectura

![big_data drawio](https://github.com/user-attachments/assets/2e10db5c-eabc-4055-adb4-af229b52cb44)

### Descripción de la Arquitectura

1.  **Orquestación (Apache Airflow):** Actúa como el cerebro del sistema, programando y automatizando la ejecución de las tareas. En este caso, se encarga de iniciar el proceso de scraping en intervalos definidos (por ejemplo, cada cierto tiempo).

2.  **Ingesta de Datos (Kafka & Tweepy):**
    *   Un script **Producer** en Python, utilizando la librería `tweepy`, se conecta a la API de Twitter para buscar tweets recientes que coincidan con palabras clave (`sismo`, `temblor`, `Perú`, etc.).
    *   Estos tweets son enviados en tiempo real al topic `tweets-eventos-sismiscos` en **Apache Kafka**, que funciona como un bus de mensajería distribuido y tolerante a fallos.
    *   Un script **Consumer** escucha este topic, recoge los tweets y los almacena en su formato crudo en una base de datos **MongoDB**, en la colección `sismos`.

3.  **Procesamiento y Transformación (ETL con Apache Spark):**
    *   Un job de **Apache Spark** se ejecuta periódicamente. Este lee los tweets no procesados de la colección `sismos`.
    *   Aplica un pipeline de transformaciones para limpiar el texto: elimina URLs, menciones, hashtags y caracteres especiales. El texto se normaliza a minúsculas.
    *   El resultado, que incluye el texto original y el `texto_limpio`, se guarda en una nueva colección de MongoDB llamada `tweets_procesados`.

4.  **Análisis con Inteligencia Artificial (LLM & Prompt Engineering):**
    *   Un script de Python lee los últimos tweets procesados de MongoDB.
    *   Se construye un **prompt** detallado que instruye a un Modelo de Lenguaje Grande (en este caso, `dolphin-llama3:8b` ejecutado localmente vía Ollama) sobre cómo analizar los datos.
    *   El LLM genera una respuesta estructurada que incluye: un insight periodístico, un resumen ejecutivo, las emociones predominantes, los daños reportados, preguntas frecuentes y etiquetas clave.
    *   Este análisis enriquecido se almacena en una colección final en MongoDB llamada `resumenes`.

5.  **Visualización (Streamlit Dashboard):**
    *   Una aplicación web construida con **Streamlit** se conecta a la colección `resumenes` de MongoDB.
    *   Presenta al usuario el último análisis generado por el LLM de forma clara e interactiva, incluyendo gráficos, mapas (con Folium) y tablas para explorar los datos en detalle.

## Descripción del dataset, origen y tamaño de data

*   **Origen:** La fuente de datos es la API de Twitter (X). Se extraen tweets públicos en español.
*   **Contenido:** El dataset consiste en objetos JSON que representan tweets. Los campos clave utilizados son el ID del tweet, el texto, el autor y la fecha de creación.
*   **Tamaño:** El tamaño de la data es dinámico y crece con cada ejecución del scraper. La estrategia de `since_id` en el productor de Kafka asegura que solo se capturen tweets nuevos, evitando duplicados y optimizando el uso de la API. En cada ciclo, se pueden capturar hasta 50 tweets nuevos.

## Herramientas y tecnologías empleadas

*   **Lenguaje de Programación:** Python 3.
*   **Orquestación:** Apache Airflow.
*   **Streaming de Datos:** Apache Kafka.
*   **Procesamiento de Datos (ETL):** Apache Spark.
*   **Base de Datos:** MongoDB (NoSQL, orientada a documentos).
*   **Inteligencia Artificial:**
    *   **Modelo:** `dolphin-llama3:8b` (una variante de Llama 3 de Meta).
    *   **Plataforma de Inferencia:** Ollama.
*   **Dashboard y Visualización:** Streamlit, Pandas, Matplotlib, Folium.
*   **Librerías Clave de Python:** `tweepy`, `kafka-python`, `pyspark`, `pymongo`, `requests`, `nltk`.

## Indicaciones de cómo ejecutar el proyecto

**Prerrequisitos:**
*   Tener instalados Docker y Docker Compose.
*   Tener Python 3.8+ y pip.
*   Una clave de Bearer Token de la API de Twitter (X), exportada como variable de entorno `X_TOKEN`.
*   Tener Ollama instalado y haber descargado el modelo: `ollama pull dolphin-llama3:8b`.

**Pasos para la ejecución:**

1.  **Levantar la infraestructura base (Kafka y MongoDB):**
    *   Utilizar un archivo `docker-compose.yml` para iniciar los servicios de Zookeeper, Kafka y MongoDB.

2.  **Instalar dependencias de Python:**
    ```bash
    pip install tweepy kafka-python pymongo pyspark confluent-kafka streamlit pandas folium matplotlib nltk
    ```

3.  **Crear el Tópico en Kafka:**
    *   Ejecutar el script `create_topic.py` (basado en el código provisto) para crear el topic `tweets-eventos-sismiscos`.

4.  **Ejecutar el pipeline de datos:**
    *   **Paso 1: Ingesta:** Ejecutar el script productor de Kafka (`producer.py`) para scrapear tweets y enviarlos al topic.
      ```bash
      python producer.py
      ```
    *   **Paso 2: Almacenamiento Crudo:** Ejecutar el script consumidor (`consumer.py`) para guardar los tweets en MongoDB.
      ```bash
      python consumer.py
      ```
    *   **Paso 3: ETL:** Ejecutar el job de Spark para limpiar los datos.
      ```bash
      spark-submit --packages org.mongodb.spark:mongo-spark-connector_2.12:10.5.0,org.mongodb:mongodb-driver-sync:4.10.2 spark_etl.py
      ```
    *   **Paso 4: Análisis con LLM:** Ejecutar el script que consulta el LLM.
      ```bash
      python llm_analysis.py
      ```

5.  **Lanzar el Dashboard:**
    *   Ejecutar la aplicación de Streamlit para visualizar los resultados.
      ```bash
      streamlit run dashboard.py
      ```

## Resultados obtenidos y análisis

El resultado principal del proyecto es un **dashboard de inteligencia en tiempo real** que transforma el caos de las redes sociales en información procesable. Los resultados clave que se pueden obtener son:

*   **Resumen Ejecutivo Automatizado:** El LLM genera un párrafo conciso y de alta calidad que resume el evento, ideal para informes rápidos o comunicados.
*   **Análisis de Sentimiento y Emociones:** En lugar de un simple "positivo/negativo", el sistema clasifica emociones específicas como "miedo", "pánico", "tranquilidad" o "confusión", ofreciendo una visión más profunda del estado de ánimo de la población.
*   **Detección Geográfica:** El sistema identifica y lista los departamentos y distritos más mencionados, lo que permite crear mapas de calor de las zonas afectadas, como se ve en la funcionalidad del mapa con Folium.
*   **Identificación de Problemas:** Extrae reportes específicos de daños (estructurales, eléctricos) y preguntas o alertas comunes de los usuarios, lo que puede ayudar a los equipos de emergencia a priorizar sus acciones.
*   **Análisis Exploratorio (EDA):** La segunda pestaña del dashboard permite analizar la volumetría de los tweets a lo largo del tiempo y las palabras más frecuentes, ayudando a identificar tendencias y temas emergentes.

## Dificultades identificadas y soluciones

1.  **Inconsistencia del LLM:**
    *   **Problema:** Los LLMs pueden ser inconsistentes en su formato de salida o "alucinar" datos (ej. `magnitud 49` en lugar de `4.9`).
    *   **Solución:** Se implementó un **prompt engineering robusto** con instrucciones claras y un formato de salida definido. Además, se añadieron funciones de post-procesamiento con **expresiones regulares (regex)** para corregir errores comunes, como en la función `corregir_magnitudes`.

2.  **Complejidad del "ruido" en los tweets:**
    *   **Problema:** Los tweets contienen jerga, memes, errores tipográficos y desinformación, lo que dificulta la extracción de datos fiables.
    *   **Solución:** Se utilizó un pipeline de limpieza en Spark para normalizar el texto. El LLM, gracias a su entrenamiento masivo, es sorprendentemente bueno para entender el contexto incluso en texto ruidoso.

3.  **Gestión de la infraestructura:**
    *   **Problema:** Levantar y conectar múltiples servicios (Kafka, Spark, MongoDB, Ollama) puede ser complejo y propenso a errores de configuración.
    *   **Solución:** La recomendación sería usar Docker y Docker Compose para encapsular cada servicio, simplificando el despliegue y garantizando la portabilidad del entorno.

4.  **Limitaciones de la API de Twitter:**
    *   **Problema:** La API tiene límites de frecuencia de consulta, lo que restringe la capacidad de obtener un flujo de datos verdaderamente en tiempo real.
    *   **Solución:** El script productor se diseñó para funcionar en ciclos, respetando los límites y utilizando el parámetro `since_id` para no solicitar datos ya procesados, maximizando la eficiencia de cada llamada.

## Conclusiones y posibles mejoras

**Conclusiones**

Este proyecto demuestra con éxito la viabilidad de construir un sistema end-to-end para el análisis de eventos de interés público a partir de redes sociales. La combinación de una arquitectura de datos robusta (Kafka, Spark, MongoDB) con el poder de análisis semántico de los LLMs permite extraer insights profundos y accionables a una velocidad y escala que serían imposibles con métodos manuales. La solución no solo presenta datos, sino que los interpreta, resume y contextualiza.

**Posibles Mejoras**

*   **Finetuning de un Modelo Especializado:** En lugar de usar un modelo generalista, se podría hacer finetuning a un modelo más pequeño (como Llama 3 8B) con un dataset curado de reportes de desastres para mejorar la precisión, reducir la latencia y los costos computacionales.
*   **Análisis de Imágenes:** Extender el sistema para analizar imágenes adjuntas en los tweets, utilizando modelos de visión por computadora para detectar daños estructurales.
*   **Sistema de Alertas Activas:** Integrar un servicio de notificaciones (ej. Telegram, SMS) que envíe alertas automáticas a partes interesadas cuando el sistema detecte un evento de alta severidad.
*   **Escalabilidad en la Nube:** Migrar la arquitectura a un proveedor cloud (AWS, GCP, Azure) utilizando servicios gestionados (ej. Amazon Kinesis para Kafka, EMR para Spark, DocumentDB para MongoDB) para mejorar la escalabilidad, la resiliencia y la facilidad de mantenimiento.
*   **Verificación de Hechos (Fact-Checking):** Añadir un módulo que cruce la información de los tweets con fuentes oficiales (como el Instituto Geofísico del Perú - IGP) para validar la información y etiquetar posibles bulos.

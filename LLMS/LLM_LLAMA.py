from pymongo import MongoClient
from datetime import datetime
import requests
import re
import json

# Conexión a MongoDB
cliente = MongoClient("mongodb://localhost:27017")
coleccion = cliente["tweets"]["tweets_procesados"]

# Leer últimos 50 tweets
tweets = list(coleccion.find().sort("fecha", -1).limit(50))
textos = [tweet["texto_limpio"] for tweet in tweets]

# Cargar listas de zonas geográficas
with open("distritos_lima.json", "r", encoding="utf-8") as f:
    distritos_lima = json.load(f)

with open("departamentos_peru.json", "r", encoding="utf-8") as f:
    departamentos_peru = json.load(f)

# Construcción del prompt
contenido_tweets = "\n".join(f"- {t}" for t in textos)

prompt_usuario = f"""
Estos son algunos tweets sobre un posible evento sísmico en Perú o Lima:

{contenido_tweets}

Realiza lo siguiente:
1. Escribe un resumen informativo como si fueras un periodista, indicando claramente lo ocurrido, el impacto, zonas afectadas, tono emocional general y posibles consecuencias.
2. Resume brevemente lo que ocurrió (evento principal, zonas, fechas).
3. Clasifica las emociones predominantes (por ejemplo: miedo, pánico, indiferencia, etc.).
4. Menciona si se reportan tipos de daño (estructural, eléctrico, etc.) y en qué zonas.
5. Extrae 2 preguntas frecuentes o alertas que los usuarios están comunicando.
6. Etiqueta automáticamente temas clave como: 'daño', 'alarma', 'zona afectada', 'desinformación', 'tranquilidad', 'reporte oficial', 'evacuación', etc.

Responde en el siguiente formato:
Insight: ...
Resumen: ...
Emociones: ...
Daños: ...
Preguntas o alertas: ...
Etiquetas: ...
"""

modelo = "dolphin-llama3:8b"  # Modelo LLaMA a usar

# Llamar al modelo LLaMA vía Ollama
response = requests.post(
    "http://localhost:11434/api/generate",
    json={"model": modelo, "prompt": prompt_usuario, "stream": False}
)

#print(response.json())


respuesta = response.json()["response"]
print("\n--- Respuesta del modelo ---\n", respuesta)

# Parseo básico del texto estructurado
def extraer_seccion(texto, seccion):
    patron = rf"{seccion}:\s*(.*?)(?=\n[A-Z]|$)"
    match = re.search(patron, texto, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else ""

# Corrección: ajustar magnitudes numéricas mal interpretadas (ej. "magnitud 49" => "magnitud 4.9")
def corregir_magnitudes(texto):
    # Caso 1: "magnitud 49" o "magnitud: 49"
    texto = re.sub(
        r"(magnitud[\s:]*)([3-9][0-9])\b",
        lambda m: f"{m.group(1)}{m.group(2)[0]}.{m.group(2)[1]}",
        texto,
        flags=re.IGNORECASE
    )

    # Caso 2: "magnitud 4.9 y 55" => normalizar ambos
    texto = re.sub(
        r"(magnitud[\s:]*[0-9]+(?:\.[0-9]+)?[\s]*(?:y|,)[\s]*)([3-9][0-9])\b",
        lambda m: f"{m.group(1)}{m.group(2)[0]}.{m.group(2)[1]}",
        texto,
        flags=re.IGNORECASE
    )

    return texto

# Corregimos tanto el insight como el resumen si existe

insight = corregir_magnitudes(extraer_seccion(respuesta, "Insight"))
resumen = corregir_magnitudes(extraer_seccion(respuesta, "Resumen"))
emociones = [e.strip() for e in extraer_seccion(respuesta, "Emociones").split(",")]
danos_raw = extraer_seccion(respuesta, "Daños")
preguntas_raw = extraer_seccion(respuesta, "Preguntas o alertas")
preguntas = re.findall(r"¿.*?\?", preguntas_raw)
etiquetas = [et.strip() for et in extraer_seccion(respuesta, "Etiquetas").split(",")]

# Procesar daños en formato estructurado (opcional: puedes mejorar este parseo)
danos_reportados = []

# Si el modelo indica "N/A" o está vacío, salta
if danos_raw.strip().lower() not in ["n/a", "ninguno", "no se reportan", ""]:
    # Busca patrones como "daño eléctrico en San Juan de Lurigancho"
    matches = re.findall(r"(daño\s+\w+)\s+en\s+([\w\s]+)", danos_raw, re.IGNORECASE)
    for tipo, zona in matches:
        danos_reportados.append({
            "tipo": tipo.strip().lower(),
            "zona": zona.strip().title()
        })

if not danos_reportados and danos_raw:
    danos_reportados.append({"tipo": "no estructurado", "detalle": danos_raw})

# Detección de zonas mencionadas
def detectar_zonas(texto, lista_zonas):
    texto_lower = texto.lower()
    zonas_detectadas = [zona for zona in lista_zonas if zona.lower() in texto_lower]
    return zonas_detectadas

zonas_distritos = detectar_zonas(respuesta, distritos_lima)
zonas_departamentos = detectar_zonas(respuesta, departamentos_peru)

# Extraer emociones individuales
emociones_tweet = {}
matches = re.findall(r"Tweet:\s*(.*?)\s*Emoción:\s*(\w+)", respuesta, re.DOTALL)
for texto, emocion in matches:
    emociones_tweet[texto.strip()] = emocion.strip().capitalize()

# Asociar emociones por tweet
tweets_emocion = []
for tweet in tweets:
    texto = tweet["texto_limpio"].strip()
    emocion = emociones_tweet.get(texto, "No detectada")
    tweets_emocion.append({"id": tweet["id"], "emocion": emocion})

# Guardar en MongoDB
coleccion_resumenes = cliente["tweets"]["resumenes"]
coleccion_resumenes.insert_one({
    "timestamp": datetime.now(),
    "modelo_usado": modelo,
    "insights": insight,
    "resumen": resumen,
    "emociones": emociones,
    "danos_reportados": danos_reportados,
    "preguntas_alertas": preguntas,
    "etiquetas": etiquetas,
    "zonas_distritos": zonas_distritos,
    "zonas_departamentos": zonas_departamentos,
    "tweets_usados": tweets_emocion
})
print("\n--- Resumen guardado en MongoDB ---")
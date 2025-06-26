from pymongo import MongoClient
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
import unicodedata

# Diccionario de emociones a emojis
emoji_emociones = {
    "miedo": "😨",
    "panico": "😱",
    "alarma": "🚨",
    "indiferencia": "😐",
    "preocupacion": "😟",
    "tranquilidad": "😌",
    "incertidumbre": "🤔",
    "confusion": "😵",
    "esperanza": "🙏",
    "enojo": "😠",
    "alivio": "😅",
    "solidaridad": "🤝"
}

def normalizar_emocion(e):
    # Remueve tildes, puntos y pasa a minúsculas
    e = e.strip().lower().replace(".", "")
    e = ''.join(c for c in unicodedata.normalize('NFD', e) if unicodedata.category(c) != 'Mn')
    return e

# solo descargar una sola vez los stopwords, si ya los tienes, comentar esta línea
try:
    stopwords_es = set(stopwords.words("spanish"))
except LookupError:
    nltk.download("stopwords")
    stopwords_es = set(stopwords.words("spanish"))

# Conectar a MongoDB
cliente = MongoClient("mongodb://localhost:27017")
db = cliente["tweets"]
coleccion = db["resumenes"]
coleccion_tweets = db["tweets_procesados"]

# Obtener todos los resúmenes
resumenes = list(coleccion.find().sort("timestamp", -1))
opciones = [f"{r['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}" for r in resumenes]

# Interfaz Streamlit
st.set_page_config(page_title="Análisis de Eventos alarmantes en el Perú", layout="wide")
st.title("🔍 Análisis de Eventos Sísmicos a partir de Tweets")

# Sidebar para selección
seccion = st.sidebar.radio("Ver:", ["Resumen general", "EDA de tweets usados"])

# Seleccionar resumen por fecha
seleccion = st.selectbox("Selecciona un resumen por fecha:", opciones)
resumen_seleccionado = next(r for r in resumenes if r['timestamp'].strftime('%Y-%m-%d %H:%M:%S') == seleccion)

if seccion == "Resumen general":
    st.subheader("🧠 Insight")
    st.info(resumen_seleccionado.get("insights", "No disponible"))

    st.subheader("📰 Resumen")
    st.write(resumen_seleccionado.get("resumen", "No disponible"))

    # Mostrar emociones con emojis
    st.subheader("💬 Emociones Detectadas")
    emociones = resumen_seleccionado.get("emociones", [])
    emociones_con_emoji = [
        f"{emoji_emociones.get(normalizar_emocion(e), '❔')} {e.strip().capitalize()}"
        for e in emociones
    ]
    st.write(", ".join(emociones_con_emoji))

    st.subheader("📍 Zonas Detectadas")
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Departamentos:**", ", ".join(resumen_seleccionado.get("zonas_departamentos", [])) or "No identificados")
    with col2:
        st.write("**Distritos:**", ", ".join(resumen_seleccionado.get("zonas_distritos", [])) or "No identificados")

    st.subheader("🏚️ Daños Reportados")
    danos = resumen_seleccionado.get("danos_reportados", [])
    if danos:
        df_danos = pd.DataFrame(danos)
        st.dataframe(df_danos)
    else:
        st.write("No se reportaron daños estructurados.")

    st.subheader("❓ Preguntas o Alertas")
    pregs = resumen_seleccionado.get("preguntas_alertas", [])
    if pregs:
        for p in pregs:
            st.markdown(f"- {p}")
    else:
        st.write("No se identificaron preguntas frecuentes.")

    st.subheader("🏷️ Etiquetas Clave")
    st.write(", ".join(resumen_seleccionado.get("etiquetas", [])))

    st.markdown("---")
    st.markdown(f"**Modelo usado:** `{resumen_seleccionado['modelo_usado']}`")
    st.markdown(f"**Total de tweets procesados:** {len(resumen_seleccionado['tweets_usados'])}")
    st.markdown(f"**Última actualización:** {resumen_seleccionado['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")

    st.subheader("🗺️ Zonas geográficas detectadas")
    coordenadas_departamentos = {
        "Lima": (-12.0464, -77.0428),
        "Callao": (-12.0500, -77.1333),
        "Ucayali": (-8.3791, -74.5539),
        "Ica": (-14.0678, -75.7286),
        "Arequipa": (-16.4090, -71.5375),
        "Cusco": (-13.5319, -71.9675),
        "Puno": (-15.8402, -70.0219),
        "Piura": (-5.1945, -80.6328),
        "Loreto": (-3.7437, -73.2516),
        "Áncash": (-9.5278, -77.5278),
        "La Libertad": (-8.1153, -79.0288),
        "San Martín": (-6.5244, -76.2959),
        "Junín": (-11.1580, -75.9928),
        "Tumbes": (-3.5669, -80.4515),
        "Huánuco": (-9.9306, -76.2422),
        "Pasco": (-10.6857, -76.2565),
        "Cajamarca": (-7.1648, -78.5100),
        "Ayacucho": (-13.1588, -74.2239),
        "Apurímac": (-14.0470, -73.0832),
        "Moquegua": (-17.1927, -70.9326),
        "Tacna": (-18.0066, -70.2463),
        "Madre de Dios": (-12.5933, -69.1869)
    }

    m = folium.Map(location=[-9.19, -75.0152], zoom_start=5)
    for zona in resumen_seleccionado.get("zonas_departamentos", []):
        coords = coordenadas_departamentos.get(zona)
        if coords:
            folium.Marker(location=coords, popup=zona, icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
    st_folium(m, width=700, height=500)

else:
    st.header("📊 Análisis Exploratorio de los Tweets Usados")
    # tweets_usados puede ser lista de IDs o lista de dicts con id+emocion
    tweets_usados = resumen_seleccionado["tweets_usados"]

    if isinstance(tweets_usados[0], dict):
        ids = [t["id"] for t in tweets_usados]
        emocion_dict = {t["id"]: t["emocion"] for t in tweets_usados}
    else:
        ids = tweets_usados
        emocion_dict = {}

    tweets_eda = list(coleccion_tweets.find({"id": {"$in": ids}}))
    df = pd.DataFrame(tweets_eda)

    # Si hay emociones, mapearlas
    if emocion_dict:
        df["emocion_detectada"] = df["id"].map(emocion_dict)

    df = pd.DataFrame(tweets_eda)

    if df.empty:
        st.warning("No hay datos disponibles para EDA.")
    else:
        st.subheader("📈 Acumulación de tweets en el tiempo")
        df_sorted = df.sort_values("fecha")
        df_sorted["acumulado"] = range(1, len(df_sorted)+1)
        st.line_chart(df_sorted.set_index("fecha")["acumulado"])

        st.subheader("🕒 Distribución temporal")
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["hora"] = df["fecha"].dt.hour
        st.bar_chart(df["hora"].value_counts().sort_index())

        st.subheader("📌 Palabras más frecuentes")

        palabras = " ".join(df["texto_limpio"].dropna()).split()
         # Extraer palabras y filtrar
        todas_las_palabras = " ".join(palabras).split()
        palabras_filtradas = [p for p in todas_las_palabras if p not in stopwords_es and len(p) > 2]
        conteo = Counter(palabras_filtradas)
        comunes = conteo.most_common(15)
        palabras, frec = zip(*comunes)
        fig, ax = plt.subplots()
        ax.barh(palabras[::-1], frec[::-1])
        ax.set_xlabel("Frecuencia")
        ax.set_title("Top 15 palabras")
        st.pyplot(fig)

        st.subheader("📍 Frecuencia por ubicación (si disponible)")
        if "ubicacion" in df.columns:
            ubicaciones = df["ubicacion"].value_counts().head(10)
            st.bar_chart(ubicaciones)

        st.subheader("📝 Vista previa de tweets")
        st.dataframe(df[["texto", "fecha"]].sort_values("fecha", ascending=False).head(10))

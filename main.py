from flask import Flask, request, Response
import requests
import os

app = Flask(__name__)

# Diccionario de radios robustas (URLs directas que SI funcionan)
RADIOS = {
    "chill": "http://stream.zeno.fm/0r0xa792kwzuv",
    "ibiza": "http://ibizaglobalradio.streaming-pro.com:8024/stream",
    "lounge": "https://streaming.brol.tech/rtfmlounge",
    "80s": "http://78.129.202.200:8030/stream",
    "rock": "http://streaming.enacast.com/lp/rockfm/mp3",
    "top40": "http://163.172.77.142:8454/stream"
}

@app.route('/')
def home():
    return "Servidor Edubot V14 - MODO RADIO DIRECTA"

@app.route('/radio')
def get_radio():
    try:
        # 1. Limpiamos la búsqueda que llega del ESP32
        query = request.args.get('url', 'chill').lower().strip()
        print(f"Peticion para: {query}")

        # 2. Buscamos en nuestro diccionario de confianza
        # Si no está en el diccionario, por defecto ponemos la de '80s' para que SIEMPRE suene algo
        audio_url = RADIOS.get(query, RADIOS["80s"])

        # 3. Túnel de datos hacia el ESP32
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(audio_url, stream=True, headers=headers, timeout=10)
        
        # Enviamos los datos en trozos pequeños para que el ESP32 no explote
        return Response(r.iter_content(chunk_size=1024), mimetype='audio/mpeg')

    except Exception as e:
        print(f"Error: {e}")
        return str(e), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

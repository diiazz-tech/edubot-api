from flask import Flask, request, Response
import requests
import os

app = Flask(__name__)

# DICCIONARIO DE RADIOS VERIFICADAS (URLs DIRECTAS MP3)
# Estas URLs son "túneles" limpios que el ESP32 puede procesar sin errores.
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
    return "Servidor Edubot V15 - BUSCADOR DE RADIOS ONLINE"

@app.route('/radio')
def get_radio():
    try:
        # 1. Obtener la palabra que envía el ESP32
        query = request.args.get('url', 'chill').lower().strip()
        print(f"Peticion recibida: {query}")

        # 2. Buscar en nuestro diccionario de radios estables
        # Si la palabra no existe en el diccionario, ponemos '80s' por defecto
        # para que el ESP32 siempre reciba datos y no de error.
        audio_url = RADIOS.get(query, RADIOS["80s"])

        # 3. Crear la conexión con el servidor de música
        # Usamos un User-Agent de navegador para evitar bloqueos (403 Forbidden)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Realizamos la petición en modo 'stream'
        r = requests.get(audio_url, stream=True, headers=headers, timeout=10)

        # 4. Enviar la respuesta al ESP32 trozo a trozo (Stream)
        # El chunk_size de 1024 es ideal para la memoria del ESP32
        def generate():
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk

        return Response(generate(), mimetype='audio/mpeg')

    except Exception as e:
        print(f"Error en el servidor: {e}")
        return str(e), 500

if __name__ == "__main__":
    # Render usa la variable de entorno PORT, si no existe usa el 10000
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

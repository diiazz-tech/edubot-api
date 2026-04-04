from flask import Flask, request, Response
import requests
import os
import yt_dlp

app = Flask(__name__)

# Diccionario base (el ESP32 enviará las palabras ya limpias)
RADIOS = {
    "chill": "http://stream.zeno.fm/0r0xa792kwzuv",
    "ibiza": "http://ibizaglobalradio.streaming-pro.com:8024/stream",
    "lounge": "https://streaming.brol.tech/rtfmlounge",
    "techno": "http://51.255.235.165:5292/stream",
    "los 40": "https://stream.zeno.fm/f3v38792kwzuv",
    "ser": "https://stream.zeno.fm/0r0xa792kwzuv"
}

def buscar_en_youtube(query):
    print(f"Buscando a fondo en YouTube: {query}")
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': False, # Habilitamos logs para ver qué pasa en Render
        'default_search': 'ytsearch1',
        'source_address': '0.0.0.0',
        'socket_timeout': 30  # Espera más tiempo a la respuesta de YT
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extraer info con reintentos automáticos
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if 'entries' in info and len(info['entries']) > 0:
                url_directa = info['entries'][0]['url']
                print(f"URL encontrada: {url_directa[:50]}...")
                return url_directa
    except Exception as e:
        print(f"Error en búsqueda YouTube: {e}")
    return None

@app.route('/')
def home(): return "Servidor Edubot V12 - MODO PACIENTE"

@app.route('/radio')
def get_radio():
    try:
        query = request.args.get('url', '').lower().strip()
        print(f"Peticion recibida del ESP32: '{query}'")

        # 1. Comprobar si es una radio fija
        audio_url = RADIOS.get(query)
        
        # 2. Si no, buscar el primer resultado en YouTube con paciencia
        if not audio_url:
            audio_url = buscar_en_youtube(query)

        if not audio_url:
            print("No se encontró nada tras la espera.")
            return "404", 404

        # Stream del audio con timeout de conexión extendido
        r = requests.get(audio_url, stream=True, timeout=60, headers={'User-Agent': 'Mozilla/5.0'})
        
        def generate():
            for chunk in r.iter_content(chunk_size=8192): # Buffer más grande
                if chunk: yield chunk
        
        return Response(generate(), mimetype='audio/mpeg')
    except Exception as e:
        print(f"Error servidor: {e}")
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

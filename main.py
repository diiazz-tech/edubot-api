from flask import Flask, request, Response
import requests
import os
import yt_dlp

app = Flask(__name__)

# RADIOS CON ENLACES DIRECTOS (PROBADOS Y ESTABLES)
RADIOS = {
    "chill": "http://stream.zeno.fm/0r0xa792kwzuv",
    "ibiza": "http://ibizaglobalradio.streaming-pro.com:8024/stream",
    "lounge": "https://streaming.brol.tech/rtfmlounge",
    "techno": "http://51.255.235.165:5292/stream",
    "los 40": "https://stream.zeno.fm/f3v38792kwzuv",
    "ser": "https://stream.zeno.fm/0r0xa792kwzuv"
}

def buscar_en_youtube(query):
    print(f"Buscando en YouTube: {query}")
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1',
        'source_address': '0.0.0.0'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if 'entries' in info and len(info['entries']) > 0:
                return info['entries'][0]['url']
    except Exception as e:
        print(f"Error en YouTube-DL: {e}")
    return None

@app.route('/')
def home():
    return "Servidor Edubot V10 - ONLINE"

@app.route('/radio')
def get_radio():
    try:
        query_raw = request.args.get('url', '').lower()
        
        # Limpieza de "paja" del dictado de voz para que la búsqueda sea limpia
        query = query_raw
        for basura in ["pon la radio ", "pon radio ", "pon la cancion ", "pon musica de ", "pon ", ".", ",", "de "]:
            query = query.replace(basura, "")
        query = query.strip()

        print(f"Peticion limpia recibida: '{query}'")

        # 1. Intentar buscar en el diccionario de radios fijas
        audio_url = RADIOS.get(query)
        
        # 2. Si no es radio, BUSQUEDA TOTAL en YouTube (sirve para canciones o directos)
        if not audio_url:
            print(f"No es radio conocida, buscando en YouTube: {query}")
            audio_url = buscar_en_youtube(query)

        if not audio_url:
            return "No se ha encontrado nada", 404

        # Realizar la petición al flujo de audio
        r = requests.get(audio_url, stream=True, timeout=20, headers={'User-Agent': 'Mozilla/5.0'})
        
        def generate():
            for chunk in r.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk
        
        return Response(generate(), mimetype='audio/mpeg')

    except Exception as e:
        print(f"Error critico en el servidor: {e}")
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

from flask import Flask, request, send_file, Response
import requests
from PIL import Image
import io
import os
import yt_dlp

app = Flask(__name__)

HEADERS = {'User-Agent': 'Mozilla/5.0'}

RADIOS = {
    "los 40": "http://directo.los40.com/los40.mp3",
    "rock fm": "https://vid.audio-stream.com:8000/rockfm.mp3",
    "chill": "http://stream.zeno.fm/0r0xa792kwzuv"
}

def buscar_en_youtube(cancion):
    ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True, 'default_search': 'ytsearch'}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{cancion}", download=False)['entries'][0]
            return info['url']
    except: return None

@app.route('/')
def home(): return "Servidor Edubot V5 - Modo Ligero"

@app.route('/radio')
def get_radio():
    try:
        query = request.args.get('url', 'chill').lower()
        audio_url = RADIOS.get(query, query)
        
        if any(x in query for x in ["pon ", "cancion"]):
            busqueda = query.replace("pon ", "").replace("cancion ", "")
            audio_url = buscar_en_youtube(busqueda)

        if not audio_url: return "404", 404

        # Reenviamos el flujo original (MP3) sin procesar nada
        r = requests.get(audio_url, stream=True, timeout=15)
        
        def generate():
            for chunk in r.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk
        
        return Response(generate(), mimetype='audio/mpeg')
    except Exception as e:
        return str(e), 500

@app.route('/foto')
def get_image():
    # Tu codigo de fotos se mantiene igual
    return "Foto OK"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

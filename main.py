from flask import Flask, request, send_file, Response
import requests
from PIL import Image
import io
import os
from pydub import AudioSegment
import yt_dlp

app = Flask(__name__)

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

RADIOS = {
    "los 40": "http://directo.los40.com/los40.mp3",
    "rock fm": "https://vid.audio-stream.com:8000/rockfm.mp3",
    "cadena dial": "https://21253.live.streamtheworld.com/CADENADIAL.mp3",
    "cadena ser": "https://cadenaser00.epimg.net/ser/directo/castillayleon/ser_valladolid.mp3",
    "cope": "https://cope-cope-rrcast.flumotion.com/cope/cope.mp3",
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
def home(): return "Servidor EduBot Online"

@app.route('/radio')
def get_radio():
    try:
        query = request.args.get('url', 'chill').lower()
        audio_url = RADIOS.get(query, query)
        
        if any(x in query for x in ["pon ", "cancion"]):
            busqueda = query.replace("pon ", "").replace("cancion ", "")
            audio_url = buscar_en_youtube(busqueda)

        if not audio_url: return "No encontrado", 404

        # Pedimos el audio original
        r = requests.get(audio_url, stream=True, timeout=15)
        
        def generate():
            # USAMOS TROZOS MÁS PEQUEÑOS (8KB) PARA NO SATURAR LA RAM DE RENDER
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    try:
                        # Convertimos el trozo a WAV (16kHz, Mono, 16-bit)
                        audio = AudioSegment.from_file(io.BytesIO(chunk))
                        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                        yield audio.raw_data
                    except:
                        # Si un trozo falla, seguimos con el siguiente en lugar de dar Error 500
                        continue
        
        return Response(generate(), mimetype='audio/wav')

    except Exception as e:
        print(f"Error: {e}")
        return "Error interno", 500

@app.route('/foto')
def get_image():
    # Tu codigo de fotos aqui se mantiene igual
    return "Foto endpoint"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

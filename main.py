from flask import Flask, request, send_file, Response
import requests
from PIL import Image
import io
import os
from pydub import AudioSegment
import yt_dlp

app = Flask(__name__)

HEADERS = {'User-Agent': 'Mozilla/5.0'}

RADIOS = {
    "los 40": "http://directo.los40.com/los40.mp3",
    "rock fm": "https://vid.audio-stream.com:8000/rockfm.mp3",
    "chill": "http://stream.zeno.fm/0r0xa792kwzuv"
}

def buscar_en_youtube(cancion):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{cancion}", download=False)['entries'][0]
            return info['url']
    except: return None

def obtener_url_v3(query):
    try:
        url_search = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&srlimit=1"
        r = requests.get(url_search, timeout=5).json()
        if r.get('query') and r['query']['search']:
            titulo = r['query']['search'][0]['title']
            url_img = f"https://es.wikipedia.org/w/api.php?action=query&titles={titulo}&prop=pageimages&format=json&pithumbsize=500"
            r_img = requests.get(url_img, timeout=5).json()
            pages = r_img.get("query", {}).get("pages", {})
            for pg in pages:
                if "thumbnail" in pages[pg]: return pages[pg]["thumbnail"]["source"]
    except: pass
    return None

@app.route('/')
def home(): return "Edubot Server OK"

@app.route('/foto')
def get_image():
    query = request.args.get('query', 'Messi')
    img_url = obtener_url_v3(query)
    if not img_url: return "404", 404
    try:
        resp = requests.get(img_url, timeout=10)
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        img = img.resize((240, 135), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=60)
        output.seek(0)
        return send_file(output, mimetype='image/jpeg')
    except: return "500", 500

@app.route('/radio')
def get_radio():
    query = request.args.get('url', 'chill').lower()
    audio_url = RADIOS.get(query, query)
    
    if any(x in query for x in ["pon ", "cancion"]):
        busqueda = query.replace("pon ", "").replace("cancion ", "")
        audio_url = buscar_en_youtube(busqueda)

    if not audio_url: return "404", 404

    try:
        # Aumentamos el timeout de la peticion inicial
        r = requests.get(audio_url, stream=True, timeout=20)
        
        def generate():
            # Usamos un buffer intermedio para pydub
            buffer = io.BytesIO()
            for chunk in r.iter_content(chunk_size=12288): # 12KB
                if chunk:
                    try:
                        # Convertimos a wav pcm 16bit 16khz mono
                        audio = AudioSegment.from_file(io.BytesIO(chunk))
                        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                        yield audio.raw_data
                    except:
                        continue
        
        return Response(generate(), mimetype='audio/wav')
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

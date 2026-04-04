from flask import Flask, request, send_file, Response
import requests
from PIL import Image
import io
import os
from pydub import AudioSegment
import yt_dlp

app = Flask(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Diccionario de radios populares
RADIOS = {
    "los 40": "http://directo.los40.com/los40.mp3",
    "rock fm": "https://vid.audio-stream.com:8000/rockfm.mp3",
    "cadena dial": "https://21253.live.streamtheworld.com/CADENADIAL.mp3",
    "cadena ser": "https://cadenaser00.epimg.net/ser/directo/castillayleon/ser_valladolid.mp3",
    "cope": "https://cope-cope-rrcast.flumotion.com/cope/cope.mp3",
    "chill": "http://stream.zeno.fm/0r0xa792kwzuv"
}

def buscar_en_youtube(cancion):
    """Busca una canción y devuelve la URL del audio"""
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch:{cancion}", download=False)['entries'][0]
        return info['url']

def obtener_url_v3(query):
    try:
        url_search = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&srlimit=1"
        r = requests.get(url_search, headers=HEADERS, timeout=5).json()
        if r.get('query') and r['query']['search']:
            titulo = r['query']['search'][0]['title']
            url_img = f"https://es.wikipedia.org/w/api.php?action=query&titles={titulo}&prop=pageimages&format=json&pithumbsize=500&redirects=1"
            r_img = requests.get(url_img, headers=HEADERS, timeout=5).json()
            pages = r_img.get("query", {}).get("pages", {})
            for pg in pages:
                if "thumbnail" in pages[pg]:
                    return pages[pg]["thumbnail"]["source"]
    except: pass
    return None

@app.route('/foto')
def get_image():
    query = request.args.get('query', 'Pedro Sanchez')
    img_url = obtener_url_v3(query)
    if not img_url: return "404", 404
    try:
        resp = requests.get(img_url, headers=HEADERS, timeout=10)
        img = Image.open(io.BytesIO(resp.content)).convert("RGB")
        img = img.resize((240, 135), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=60) # Calidad 60 para que pese menos
        output.seek(0)
        return send_file(output, mimetype='image/jpeg')
    except: return "500", 500

@app.route('/radio')
def get_radio():
    query = request.args.get('url', 'chill').lower()
    
    # 1. ¿Es una radio guardada?
    if query in RADIOS:
        audio_url = RADIOS[query]
    # 2. ¿Es una petición de canción (ej: "pon funky town")?
    elif "pon " in query or "cancion" in query:
        busqueda = query.replace("pon ", "").replace("la cancion ", "")
        try:
            audio_url = buscar_en_youtube(busqueda)
        except:
            audio_url = RADIOS["chill"]
    else:
        audio_url = query

    try:
        r = requests.get(audio_url, stream=True, timeout=15)
        def generate():
            # Enviamos bloques de 16KB para que la ESP32 no se sature
            for chunk in r.iter_content(chunk_size=16384):
                if chunk:
                    try:
                        audio = AudioSegment.from_file(io.BytesIO(chunk))
                        # OPTIMIZACIÓN EXTREMA PARA ESP32:
                        # 16000Hz, Mono, 16 bits (Lo más liviano que suena bien)
                        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                        yield audio.raw_data
                    except: continue
        return Response(generate(), mimetype='audio/wav')
    except: return "Error", 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

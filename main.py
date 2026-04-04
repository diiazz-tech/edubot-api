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
    """Busca una canción y devuelve la URL directa del flujo de audio"""
    print(f"Buscando en YouTube: {cancion}")
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch',
        'source_address': '0.0.0.0' # Evita errores de red en Render
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{cancion}", download=False)['entries'][0]
            return info['url']
    except Exception as e:
        print(f"Error buscando en YouTube: {e}")
        return None

def obtener_url_v3(query):
    # 1. Intento con Wikipedia
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
        img.save(output, format='JPEG', quality=60)
        output.seek(0)
        return send_file(output, mimetype='image/jpeg')
    except: return "500", 500

@app.route('/radio')
def get_radio():
    query = request.args.get('url', 'chill').lower()
    
    # Lógica de selección de fuente
    audio_url = None
    
    # 1. Comprobar si es una radio del diccionario
    if query in RADIOS:
        audio_url = RADIOS[query]
        print(f"Modo: Radio Guardada ({query})")
    
    # 2. Comprobar si es una petición de canción
    elif any(x in query for x in ["pon ", "cancion", "musica"]):
        busqueda = query.replace("pon ", "").replace("la cancion ", "").replace("musica ", "")
        audio_url = buscar_en_youtube(busqueda)
        print(f"Modo: YouTube ({busqueda})")
    
    # 3. Si no, tratar como URL directa
    else:
        audio_url = query
        print(f"Modo: URL Directa")

    if not audio_url:
        audio_url = RADIOS["chill"]

    try:
        # stream=True es vital para no saturar el servidor
        r = requests.get(audio_url, stream=True, timeout=20)
        
        def generate():
            # USAMOS UN CHUNK PEQUEÑO (8192) PARA UN FLUJO CONSTANTE (BIT A BIT)
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    try:
                        # Convertimos el pequeño bloque a WAV PCM instantáneamente
                        audio = AudioSegment.from_file(io.BytesIO(chunk))
                        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                        yield audio.raw_data
                    except:
                        continue
        
        return Response(generate(), mimetype='audio/wav')

    except Exception as e:
        print(f"Error en streaming: {e}")
        return "Error", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

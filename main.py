from flask import Flask, request, send_file, Response
import requests
from PIL import Image
import io
import os
from pydub import AudioSegment
import yt_dlp

app = Flask(__name__)

# Cabeceras para simular un navegador real
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
    "chill": "http://stream.zeno.fm/0r0xa792kwzuv",
    "virgin": "http://icecast.unitedradio.it/Virgin.mp3"
}

def buscar_en_youtube(cancion):
    """Busca una canción y devuelve la URL directa del flujo de audio"""
    print(f"Buscando en YouTube: {cancion}")
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch',
        'source_address': '0.0.0.0'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{cancion}", download=False)['entries'][0]
            return info['url']
    except Exception as e:
        print(f"Error buscando en YouTube: {e}")
        return None

def obtener_url_v3(query):
    """Busca imágenes en Wikipedia"""
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
    
    # Decidir fuente
    if any(x in query for x in ["pon ", "cancion", "musica"]):
        busqueda = query.replace("pon ", "").replace("la cancion ", "").replace("musica ", "")
        audio_url = buscar_en_youtube(busqueda)
    else:
        audio_url = RADIOS.get(query, query)

    if not audio_url:
        return "No se encontró audio", 404

    try:
        r = requests.get(audio_url, stream=True, timeout=15)
        
        def generate():
            # Usamos fragmentos de 8KB
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    try:
                        audio = AudioSegment.from_file(io.BytesIO(chunk))
                        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                        yield audio.raw_data
                    except:
                        continue
        
        return Response(generate(), mimetype='audio/wav', headers={
            'Cache-Control': 'no-cache',
            'Transfer-Encoding': 'chunked',
            'Connection': 'keep-alive'
        })
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == "__main__":
    # Prioridad absoluta al puerto que asigne Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)

from flask import Flask, request, send_file, Response
import requests
from PIL import Image
import io
import os
from pydub import AudioSegment

app = Flask(__name__)

# Cabeceras para engañar a los servidores y que crean que somos un usuario real
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def obtener_url_v3(query):
    # 1. Intento con Wikipedia (Búsqueda refinada)
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

    # 2. Intento con Pixabay (Plan B)
    try:
        url_pixa = f"https://pixabay.com/api/?key=55285511-94ca0ba1f043883f1b1f4f57a&q={query}&image_type=photo"
        r_p = requests.get(url_pixa, headers=HEADERS, timeout=5).json()
        if r_p.get('hits'):
            return r_p['hits'][0]['webformatURL']
    except: pass

    return None

@app.route('/foto')
def get_image():
    query = request.args.get('query', 'Pedro Sanchez')
    print(f"Peticion para: {query}")

    img_url = obtener_url_v3(query)
    if not img_url:
        return f"No se encontro URL para: {query}", 404

    try:
        # Descarga con cabeceras de navegador
        resp = requests.get(img_url, headers=HEADERS, timeout=15)
        
        # Verificamos si realmente hemos bajado una imagen
        content_type = resp.headers.get('Content-Type', '')
        if 'image' not in content_type:
            return f"Error: Lo descargado no es una imagen, es {content_type}", 500

        # PROCESADO TOTAL
        img = Image.open(io.BytesIO(resp.content))
        img = img.convert("RGB")
        img = img.resize((240, 135), Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=75)
        output.seek(0)
        
        return send_file(output, mimetype='image/jpeg')
        
    except Exception as e:
        return f"Fallo final: {str(e)}", 500

# --- NUEVA FUNCIÓN PARA RADIO (MP3 A WAV) ---
@app.route('/radio')
def get_radio():
    # URL de una emisora por defecto (puedes pasar otra por el parámetro ?url=)
    radio_url = request.args.get('url', 'http://stream.zeno.fm/0r0xa792kwzuv')
    
    try:
        # Conexión al stream de la radio
        r = requests.get(radio_url, stream=True, timeout=10)
        
        def generate():
            # Procesamos el stream por bloques para no saturar la RAM
            for chunk in r.iter_content(chunk_size=64000):
                if chunk:
                    try:
                        # Convertimos el bloque MP3 a WAV (16kHz, Mono, 16bit)
                        audio = AudioSegment.from_file(io.BytesIO(chunk), format="mp3")
                        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
                        
                        # Extraemos los bytes crudos (PCM)
                        raw_data = io.BytesIO()
                        audio.export(raw_data, format="wav")
                        yield raw_data.getvalue()
                    except:
                        continue # Si un bloque falla, pasamos al siguiente
        
        return Response(generate(), mimetype='audio/wav')

    except Exception as e:
        return f"Error en radio: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

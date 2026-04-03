from flask import Flask, request, send_file
import requests
from PIL import Image
import io
import os

app = Flask(__name__)

def obtener_url_universal(busqueda):
    headers = {'User-Agent': 'EduBot/1.0'}
    # 1. Buscamos en Wikipedia (Plan A para personajes/historia)
    try:
        search_url = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={busqueda}&format=json&srlimit=1"
        res = requests.get(search_url, headers=headers, timeout=5).json()
        if res.get('query') and res['query']['search']:
            titulo = res['query']['search'][0]['title']
            img_api = f"https://es.wikipedia.org/w/api.php?action=query&titles={titulo}&prop=pageimages&format=json&pithumbsize=500&redirects=1"
            data = requests.get(img_api, headers=headers, timeout=5).json()
            pages = data.get("query", {}).get("pages", {})
            for pg in pages:
                if "thumbnail" in pages[pg]:
                    return pages[pg]["thumbnail"]["source"]
    except: pass

    # 2. Si Wikipedia falla, usamos Pixabay (Plan B para cosas generales)
    try:
        pixa_url = f"https://pixabay.com/api/?key=55285511-94ca0ba1f043883f1b1f4f57a&q={busqueda}&image_type=photo&per_page=3"
        res_pixa = requests.get(pixa_url, timeout=5).json()
        if res_pixa.get('hits'):
            return res_pixa['hits'][0]['webformatURL']
    except: pass
    
    return None

@app.route('/foto')
def get_image():
    query = request.args.get('query', 'robot')
    print(f"Traduciendo imagen para: {query}")
    
    img_url = obtener_url_universal(query)
    if not img_url:
        return "No encontre ninguna imagen", 404

    try:
        # DESCARGA UNIVERSAL
        response = requests.get(img_url, timeout=15)
        raw_data = io.BytesIO(response.content)
        
        # PROCESADO TODOTERRENO (PIL detecta el formato solo: BMP, PNG, JPG, etc.)
        img = Image.open(raw_data)
        
        # Convertimos a RGB (Esto elimina transparencias de PNG y arregla BMPs extraños)
        img = img.convert("RGB")
        
        # REDIMENSIÓN EXACTA PARA ESP32
        img = img.resize((240, 135), Image.Resampling.LANCZOS)
        
        # EMPAQUETADO FINAL (Siempre sale como JPEG para que el ESP32 no se líe)
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=75)
        output.seek(0)
        
        return send_file(output, mimetype='image/jpeg')
        
    except Exception as e:
        return f"Fallo al traducir imagen: {str(e)}", 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

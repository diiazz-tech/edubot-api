from flask import Flask, request, send_file
import requests
from PIL import Image
import io
import os

app = Flask(__name__)

# Tu llave de Pixabay por si Wikipedia falla
PIXABAY_KEY = "55285511-94ca0ba1f043883f1b1f4f57a"

def buscar_en_wikipedia(query):
    try:
        # 1. Buscamos el título exacto en Wikipedia
        search_url = f"https://es.wikipedia.org/w/api.php?action=query&titles={query}&prop=pageimages&format=json&pithumbsize=500&redirects=1"
        r = requests.get(search_url, timeout=5)
        data = r.json()
        pages = data.get("query", {}).get("pages", {})
        for pg in pages:
            if "thumbnail" in pages[pg]:
                return pages[pg]["thumbnail"]["source"]
        return None
    except:
        return None

@app.route('/foto')
def get_image():
    query = request.args.get('query', 'robot')
    print(f"Buscando: {query}")
    
    # INTENTO 1: Wikipedia (Para famosos/personajes)
    img_url = buscar_en_wikipedia(query)
    
    # INTENTO 2: Pixabay (Si Wikipedia no tiene nada)
    if not img_url:
        print("Wikipedia falló, intentando Pixabay...")
        search_url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={query}&image_type=photo&orientation=horizontal&per_page=3"
        r = requests.get(search_url)
        data = r.json()
        if data.get("hits"):
            img_url = data["hits"][0]["webformatURL"]

    if img_url:
        try:
            img_r = requests.get(img_url, timeout=10)
            img = Image.open(io.BytesIO(img_r.content))
            img = img.convert("RGB")
            
            # Redimensionar a tu pantalla 240x135
            img = img.resize((240, 135), Image.Resampling.LANCZOS)
            
            img_io = io.BytesIO()
            img.save(img_io, 'JPEG', quality=65)
            img_io.seek(0)
            return send_file(img_io, mimetype='image/jpeg')
        except Exception as e:
            return str(e), 500
            
    return "No encontré nada", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

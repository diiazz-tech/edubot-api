from flask import Flask, request, send_file
import requests
from PIL import Image
import io
import os

app = Flask(__name__)

PIXABAY_KEY = "55285511-94ca0ba1f043883f1b1f4f57a"

def buscar_en_wikipedia(query):
    print(f"Buscando en Wikipedia: {query}")
    for lang in ['es', 'en']:
        try:
            # 1. Buscar la página más parecida (Search)
            search_url = f"https://{lang}.wikipedia.org/w/api.php?action=opensearch&search={query}&limit=1&format=json"
            s_res = requests.get(search_url, timeout=5).json()
            
            if s_res[1]:
                titulo_real = s_res[1][0]
                # 2. Sacar la foto de ese título (PageImages)
                img_url = f"https://{lang}.wikipedia.org/w/api.php?action=query&titles={titulo_real}&prop=pageimages&format=json&pithumbsize=500&redirects=1"
                data = requests.get(img_url, timeout=5).json()
                pages = data.get("query", {}).get("pages", {})
                for pg in pages:
                    if "thumbnail" in pages[pg]:
                        return pages[pg]["thumbnail"]["source"]
        except:
            continue
    return None

@app.route('/foto')
def get_image():
    raw_query = request.args.get('query', 'robot').lower()
    
    # Limpiar frases típicas
    query = raw_query
    for word in ["foto de", "imagen de", "enseña", "busca"]:
        query = query.replace(word, "")
    query = query.strip()

    # Paso 1: Wikipedia con búsqueda inteligente
    img_url = buscar_en_wikipedia(query)
    
    # Paso 2: Pixabay si lo anterior falla
    if not img_url:
        print("Fallo Wikipedia, a por Pixabay...")
        url_pixa = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={query.replace(' ', '+')}&image_type=photo&per_page=3"
        try:
            data = requests.get(url_pixa).json()
            if data.get("hits"):
                img_url = data["hits"][0]["webformatURL"]
        except: pass

    if img_url:
        try:
            img_r = requests.get(img_url, timeout=10)
            img = Image.open(io.BytesIO(img_r.content)).convert("RGB")
            
            # Recorte inteligente 240x135
            w, h = img.size
            target = 240/135
            if w/h > target:
                new_w = int(target * h)
                off = (w - new_w) // 2
                img = img.crop((off, 0, w - off, h))
            else:
                new_h = int(w / target)
                off = (h - new_h) // 2
                img = img.crop((0, off, w, h - off))

            img = img.resize((240, 135), Image.Resampling.LANCZOS)
            out = io.BytesIO()
            img.save(out, 'JPEG', quality=75)
            out.seek(0)
            return send_file(out, mimetype='image/jpeg')
        except: return "Error procesando", 500
            
    return "Nada encontrado", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

from flask import Flask, request, send_file
import requests
from PIL import Image
import io
import os

app = Flask(__name__)

PIXABAY_KEY = "55285511-94ca0ba1f043883f1b1f4f57a"

def buscar_foto_wikipedia(query):
    # Ponemos la primera letra en mayúscula para que Wikipedia lo entienda mejor
    query = query.title() 
    print(f"Intentando Wikipedia con: {query}")
    
    # Probamos en Wikipedia en español y luego en inglés
    for lang in ['es', 'en']:
        try:
            url = f"https://{lang}.wikipedia.org/w/api.php?action=query&titles={query}&prop=pageimages&format=json&pithumbsize=500&redirects=1"
            r = requests.get(url, timeout=5)
            data = r.json()
            pages = data.get("query", {}).get("pages", {})
            for pg in pages:
                if "thumbnail" in pages[pg]:
                    return pages[pg]["thumbnail"]["source"]
        except:
            continue
    return None

@app.route('/foto')
def get_image():
    query = request.args.get('query', 'robot').strip()
    
    # Limpiamos palabras como "foto de", "enseña", etc.
    for word in ["foto de", "imagen de", "enseña", "busca"]:
        query = query.lower().replace(word, "").strip()

    # 1. Intentar Wikipedia (Famosos)
    img_url = buscar_foto_wikipedia(query)
    
    # 2. Intentar Pixabay (Cosas generales)
    if not img_url:
        print("Wikipedia falló, usando Pixabay...")
        url_pixa = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={query.replace(' ', '+')}&image_type=photo&orientation=horizontal&per_page=3"
        try:
            r = requests.get(url_pixa)
            data = r.json()
            if data.get("hits"):
                img_url = data["hits"][0]["webformatURL"]
        except:
            pass

    if img_url:
        try:
            img_r = requests.get(img_url, timeout=10)
            img = Image.open(io.BytesIO(img_r.content))
            img = img.convert("RGB")
            
            # CROP INTELIGENTE: Para que no se vea estirado
            ancho, alto = img.size
            target_ratio = 240/135
            actual_ratio = ancho/alto
            
            if actual_ratio > target_ratio:
                new_width = int(target_ratio * alto)
                offset = (ancho - new_width) // 2
                img = img.crop((offset, 0, ancho - offset, alto))
            else:
                new_height = int(ancho / target_ratio)
                offset = (alto - new_height) // 2
                img = img.crop((0, offset, ancho, alto - offset))

            img = img.resize((240, 135), Image.Resampling.LANCZOS)
            
            img_io = io.BytesIO()
            img.save(img_io, 'JPEG', quality=70)
            img_io.seek(0)
            return send_file(img_io, mimetype='image/jpeg')
        except Exception as e:
            return f"Error procesando: {e}", 500
            
    return "No encontré nada", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

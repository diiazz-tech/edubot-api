from flask import Flask, request, send_file
import requests
from PIL import Image
import io
import os

app = Flask(__name__)

def obtener_foto_wikipedia(busqueda):
    # 1. Buscamos el título correcto en Wikipedia
    # Usamos un User-Agent para que Wikipedia no nos bloquee
    headers = {'User-Agent': 'EduBot/1.0 (contacto: tu-email@ejemplo.com)'}
    search_url = f"https://es.wikipedia.org/w/api.php?action=query&list=search&srsearch={busqueda}&format=json&srlimit=1"
    
    try:
        r = requests.get(search_url, headers=headers, timeout=10)
        if r.status_code != 200:
            return None
        
        res = r.json()
        if not res.get('query') or not res['query']['search']:
            return None
            
        titulo = res['query']['search'][0]['title']
        
        # 2. Obtenemos la URL de la imagen de ese título
        img_api = f"https://es.wikipedia.org/w/api.php?action=query&titles={titulo}&prop=pageimages&format=json&pithumbsize=500&redirects=1"
        data = requests.get(img_api, headers=headers, timeout=10).json()
        
        pages = data.get("query", {}).get("pages", {})
        for pg in pages:
            if "thumbnail" in pages[pg]:
                return pages[pg]["thumbnail"]["source"]
    except Exception as e:
        print(f"Error en Wikipedia: {e}")
        return None
    return None

@app.route('/foto')
def get_image():
    # El valor por defecto ahora es Pedro Sanchez para probar rápido
    query = request.args.get('query', 'Pedro Sanchez')
    print(f"Buscando foto de: {query}")
    
    url_final = obtener_foto_wikipedia(query)
    
    if url_final:
        try:
            img_r = requests.get(url_final, timeout=15)
            img = Image.open(io.BytesIO(img_r.content)).convert("RGB")
            
            # Ajuste 240x135 para el ESP32
            img = img.resize((240, 135), Image.Resampling.LANCZOS)
            
            out = io.BytesIO()
            img.save(out, 'JPEG', quality=85)
            out.seek(0)
            return send_file(out, mimetype='image/jpeg')
        except:
            return "Error procesando la imagen", 500
    
    return f"No se encontro ninguna foto para: {query}", 404

if __name__ == "__main__":
    # Render usa el puerto que le da la gana, así que lo leemos de las variables
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

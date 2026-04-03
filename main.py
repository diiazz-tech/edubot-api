from flask import Flask, request, send_file
import requests
from PIL import Image
import io
import os

app = Flask(__name__)

@app.route('/foto')
def get_image():
    query = request.args.get('query', 'Pedro Sanchez').title()
    print(f"Buscando a: {query}")
    
    # Buscador directo de Wikipedia
    url = f"https://es.wikipedia.org/w/api.php?action=query&titles={query}&prop=pageimages&format=json&pithumbsize=500&redirects=1"
    
    try:
        data = requests.get(url).json()
        pages = data.get("query", {}).get("pages", {})
        img_url = None
        for pg in pages:
            if "thumbnail" in pages[pg]:
                img_url = pages[pg]["thumbnail"]["source"]
        
        if img_url:
            img_r = requests.get(img_url)
            img = Image.open(io.BytesIO(img_r.content)).convert("RGB")
            img = img.resize((240, 135), Image.Resampling.LANCZOS)
            out = io.BytesIO()
            img.save(out, 'JPEG', quality=80)
            out.seek(0)
            return send_file(out, mimetype='image/jpeg')
        
        return f"Wikipedia no tiene foto para {query}", 404
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

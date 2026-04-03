from flask import Flask, request, send_file
import requests
from PIL import Image
import io
import os

app = Flask(__name__)

# Tu API de Pixabay ya configurada
PIXABAY_KEY = "55285511-94ca0ba1f043883f1b1f4f57a"

@app.route('/foto')
def get_image():
    # El ESP32 enviará: /foto?query=loquezea
    query = request.args.get('query', 'robot')
    print(f"Buscando en Pixabay: {query}")
    
    # 1. Buscamos en Pixabay (pedimos fotos seguras y horizontales)
    search_url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={query}&image_type=photo&orientation=horizontal&per_page=3&safesearch=true"
    
    try:
        r = requests.get(search_url, timeout=10)
        data = r.json()
        
        if data.get("hits"):
            # Elegimos la mejor URL (webformatURL suele ser de ~640px, perfecta para procesar)
            img_url = data["hits"][0]["webformatURL"]
            
            # 2. Descargamos la imagen real
            img_r = requests.get(img_url, timeout=10)
            img = Image.open(io.BytesIO(img_r.content))
            
            # 3. PROCESAMIENTO CRÍTICO:
            # Convertimos a RGB (por si viene un PNG con transparencia que rompa el ESP32)
            img = img.convert("RGB")
            # Redimensionamos exactamente al tamaño de tu ST7789 (240x135)
            img = img.resize((240, 135), Image.Resampling.LANCZOS)
            
            # 4. Guardamos como JPEG optimizado
            img_io = io.BytesIO()
            # Calidad 60 es el punto dulce: se ve bien y pesa poquísimo (~8KB)
            img.save(img_io, 'JPEG', quality=60)
            img_io.seek(0)
            
            print("¡Imagen procesada y enviada!")
            return send_file(img_io, mimetype='image/jpeg')
        else:
            return "No encontré resultados", 404
            
    except Exception as e:
        print(f"Error en el servidor: {e}")
        return str(e), 500

if __name__ == "__main__":
    # Render asigna un puerto dinámico, esto es obligatorio para que funcione allí
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

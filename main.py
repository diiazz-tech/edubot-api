from flask import Flask, request, Response
import requests
import os
import yt_dlp

app = Flask(__name__)

# Usamos URLs que sabemos que NO tienen geobloqueo
RADIOS = {
    "chill": "http://stream.zeno.fm/0r0xa792kwzuv",
    "ibiza": "http://ibizaglobalradio.streaming-pro.com:8024/stream",
    "lounge": "https://streaming.brol.tech/rtfmlounge",
    "techno": "http://51.255.235.165:5292/stream"
}

def buscar_en_youtube(query):
    # Opciones ultra-compatibles para Render
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1',
        'nocheckcertificate': True,
        'source_address': '0.0.0.0'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if 'entries' in info:
                return info['entries'][0]['url']
    except Exception as e:
        print(f"Error YT: {e}")
    return None

@app.route('/')
def home(): return "Servidor Edubot V13 - FIX DATA"

@app.route('/radio')
def get_radio():
    query = request.args.get('url', 'chill').lower().strip()
    
    # Prioridad 1: Diccionario
    audio_url = RADIOS.get(query)
    
    # Prioridad 2: YouTube
    if not audio_url:
        audio_url = buscar_en_youtube(query)
    
    if not audio_url:
        return "No encontrado", 404

    # Peticion con cabeceras de navegador real para que no nos bloqueen
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        # Importante: timeout corto para conectar, pero largo para leer
        r = requests.get(audio_url, stream=True, headers=headers, timeout=(5, 60))
        
        def generate():
            # Si el servidor de origen no responde, esto soltara una excepcion
            for chunk in r.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk
        
        return Response(generate(), mimetype='audio/mpeg')
    except:
        return "Error de conexion al origen", 502

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

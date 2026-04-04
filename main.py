from flask import Flask, request, Response
import requests
import os
import yt_dlp

app = Flask(__name__)

RADIOS = {
    "los 40": "http://directo.los40.com/los40.mp3",
    "rock fm": "https://vid.audio-stream.com:8000/rockfm.mp3",
    "chill": "http://stream.zeno.fm/0r0xa792kwzuv",
    "cope": "https://cope-cope-rrcast.flumotion.com/cope/cope.mp3"
}

def buscar_en_youtube(cancion):
    ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True, 'default_search': 'ytsearch'}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{cancion}", download=False)['entries'][0]
            return info['url']
    except: return None

@app.route('/')
def home(): return "Servidor Edubot V6 - ONLINE"

@app.route('/radio')
def get_radio():
    try:
        query = request.args.get('url', 'chill').lower()
        # Limpiamos la paja que manda el ESP32
        query = query.replace("de ", "").replace("la ", "").replace(".", "").strip()
        
        audio_url = RADIOS.get(query, query)
        
        # Si parece una búsqueda de canción
        if len(query) > 3 and query not in RADIOS:
            audio_url = buscar_en_youtube(query)

        if not audio_url: return "No encontrado", 404

        # REENVÍO DIRECTO (Sin procesar nada, gasta 0 RAM)
        r = requests.get(audio_url, stream=True, timeout=10)
        
        def generate():
            for chunk in r.iter_content(chunk_size=4096):
                if chunk: yield chunk
        
        return Response(generate(), mimetype='audio/mpeg')

    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

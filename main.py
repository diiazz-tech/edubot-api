from flask import Flask, request, Response
import requests
import os
import yt_dlp

app = Flask(__name__)

# Diccionario con nombres exactos para evitar fallos
RADIOS = {
    "los 40": "http://directo.los40.com/los40.mp3",
    "rock fm": "https://vid.audio-stream.com:8000/rockfm.mp3",
    "chill": "http://stream.zeno.fm/0r0xa792kwzuv",
    "cope": "https://cope-cope-rrcast.flumotion.com/cope/cope.mp3",
    "ser": "https://cadenaser00.epimg.net/ser/directo/castillayleon/ser_valladolid.mp3"
}

def buscar_en_youtube(cancion):
    print(f"Buscando en YouTube: {cancion}")
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch',
        'source_address': '0.0.0.0' # Obligatorio para evitar bloqueos en Render
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_results = ydl.extract_info(f"ytsearch:{cancion}", download=False)
            if 'entries' in search_results and len(search_results['entries']) > 0:
                return search_results['entries'][0]['url']
    except Exception as e:
        print(f"Error YT: {e}")
    return None

@app.route('/')
def home():
    return "Servidor Edubot V7 - ONLINE"

@app.route('/radio')
def get_radio():
    try:
        # 1. Cogemos la URL y limpiamos TODO lo que sobra
        query = request.args.get('url', '').lower()
        
        # Limpieza extrema de caracteres que ensucian la URL
        for basura in ["de ", "la ", "el ", "pon ", "musica ", "cancion ", ".", ",", "!", "?"]:
            query = query.replace(basura, "")
        
        query = query.strip()
        print(f"Peticion final limpia: '{query}'")

        if not query:
            return "Query vacia", 400

        # 2. ¿Es una radio del diccionario?
        audio_url = RADIOS.get(query)
        
        # 3. Si no es radio, buscamos en YouTube
        if not audio_url:
            audio_url = buscar_en_youtube(query)

        if not audio_url:
            print("No se encontro nada en YouTube")
            return "No encontrado", 404

        # 4. Reenvio directo (MP3)
        r = requests.get(audio_url, stream=True, timeout=15)
        
        def generate():
            for chunk in r.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk
        
        return Response(generate(), mimetype='audio/mpeg')

    except Exception as e:
        print(f"Error interno: {e}")
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

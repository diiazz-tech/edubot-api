from flask import Flask, request, Response
import requests
import os
import yt_dlp

app = Flask(__name__)

RADIOS = {
    "chill": "http://stream.zeno.fm/0r0xa792kwzuv",
    "ibiza": "http://ibizaglobalradio.streaming-pro.com:8024/stream",
    "lounge": "https://streaming.brol.tech/rtfmlounge"
}

def buscar_en_youtube(query):
    # Configuracion especial para NO usar FFmpeg
    ydl_opts = {
        'format': 'bestaudio/best', # Busca el mejor audio directo
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1',
        'nocheckcertificate': True,
        'prefer_ffmpeg': False  # <--- CLAVE: No intenta usar FFmpeg
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if 'entries' in info:
                # Retornamos la URL directa del flujo de Google
                return info['entries'][0]['url']
    except Exception as e:
        print(f"Error YT: {e}")
    return None

@app.route('/radio')
def get_radio():
    try:
        query = request.args.get('url', 'chill').lower().strip()
        print(f"Peticion: {query}")
        
        # 1. Diccionario
        audio_url = RADIOS.get(query)
        
        # 2. YouTube si no esta en el diccionario
        if not audio_url:
            audio_url = buscar_en_youtube(query)
        
        if not audio_url:
            return "No encontrado en YT", 404

        # 3. Reenvio del flujo
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(audio_url, stream=True, headers=headers, timeout=15)
        
        return Response(r.iter_content(chunk_size=2048), mimetype='audio/mpeg')
    except Exception as e:
        return str(e), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

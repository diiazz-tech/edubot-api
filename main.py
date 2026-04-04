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
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1',
        'nocheckcertificate': True
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if 'entries' in info:
                return info['entries'][0]['url']
    except: return None

@app.route('/radio')
def get_radio():
    query = request.args.get('url', 'chill').lower().strip()
    audio_url = RADIOS.get(query, buscar_en_youtube(query))
    
    if not audio_url: return "No encontrado", 404

    # Enviamos el chorro de datos. 
    # El secreto es que el ESP32 necesita paquetes limpios.
    r = requests.get(audio_url, stream=True, timeout=20)
    return Response(r.iter_content(chunk_size=1024), mimetype='audio/mpeg')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

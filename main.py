from flask import Flask, request, Response
import requests
import os
import yt_dlp

app = Flask(__name__)

# Radios fijas por si falla YouTube
RADIOS = {
    "chill": "http://stream.zeno.fm/0r0xa792kwzuv",
    "ibiza": "http://ibizaglobalradio.streaming-pro.com:8024/stream",
    "80s": "http://78.129.202.200:8030/stream"
}

def buscar_en_youtube(query):
    ydl_opts = {
        'format': 'bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'default_search': 'ytsearch1',
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=False)
            if 'entries' in info:
                return info['entries'][0]['url']
    except Exception as e:
        print(f"Error YT: {e}")
    return None

@app.route('/radio')
def get_radio():
    query = request.args.get('url', 'chill').lower().strip()
    
    # 1. Si es radio fija
    audio_url = RADIOS.get(query)
    
    # 2. Si no, BUSCAR EN YOUTUBE
    if not audio_url:
        audio_url = buscar_en_youtube(query)
    
    if not audio_url:
        return "No encontrado", 404

    # Enviar el chorro de datos MP3
    r = requests.get(audio_url, stream=True, timeout=15)
    return Response(r.iter_content(chunk_size=512), mimetype='audio/mpeg')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

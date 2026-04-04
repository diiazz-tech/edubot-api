import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import yt_dlp
import subprocess

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Edubot API funcionando"}

@app.get("/radio")
async def radio(url: str):
    try:
        # 1. Buscar el audio en YouTube
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'default_search': 'ytsearch',
            'nocheckcertificate': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch:{url}"
            info = ydl.extract_info(search_query, download=False)
            if not info or 'entries' not in info or len(info['entries']) == 0:
                raise HTTPException(status_code=404, detail="No se encontró el audio")
            
            audio_url = info['entries'][0]['url']

        # 2. Configurar FFmpeg para convertir a PCM S16LE (16kHz, Mono)
        # Este es el formato EXACTO que espera el I2S de tu ESP32
        ffmpeg_command = [
            'ffmpeg',
            '-i', audio_url,
            '-f', 's16le',        # PCM 16-bit Little Endian
            '-acodec', 'pcm_s16le',
            '-ar', '16000',       # 16kHz
            '-ac', '1',           # Mono
            '-'                   # Salida a stdout
        ]

        process = subprocess.Popen(
            ffmpeg_command, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.DEVNULL
        )

        def iter_audio():
            try:
                while True:
                    chunk = process.stdout.read(4096)
                    if not chunk:
                        break
                    yield chunk
            finally:
                process.kill()

        return StreamingResponse(iter_audio(), media_type="audio/basic")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

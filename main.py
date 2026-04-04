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

        ffmpeg_command = [
            'ffmpeg',
            '-i', audio_url,
            '-filter:a', 'volume=3.0',
            '-f', 's16le',
            '-acodec', 'pcm_s16le',
            '-ar', '16000',
            '-ac', '1',
            '-'
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

        # Cambio a application/octet-stream para asegurar flujo de datos binarios puro
        return StreamingResponse(iter_audio(), media_type="application/octet-stream")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

FROM python:3.11-slim

# Instalar FFmpeg para el audio
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Instalar librerías
RUN pip install --no-cache-dir -r requirements.txt

# Puerto que usa Render
EXPOSE 10000

# Comando para arrancar
CMD ["python", "main.py"]

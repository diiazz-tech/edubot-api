FROM python:3.11-slim

# Instalar FFmpeg (el motor de audio)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Instalar las librerías de Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para arrancar tu app
CMD ["python", "main.py"]

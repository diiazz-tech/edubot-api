FROM python:3.11-slim

# Instalar FFmpeg y dependencias de sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

# Instalar librerías de Python
RUN pip install --no-cache-dir -r requirements.txt

# Puerto de Render
EXPOSE 10000

CMD ["python", "main.py"]

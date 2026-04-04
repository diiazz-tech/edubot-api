FROM python:3.11-slim

# Instalar FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Configurar el directorio de trabajo
WORKDIR /app
COPY . .

# Instalar librerías de Python
RUN pip install --no-cache-dir -r requirements.txt

# Comando para ejecutar la app
CMD ["python", "main.py"]

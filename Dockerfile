FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema (para chromadb y otras librerías)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements.txt primero (para aprovechar cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Puerto de Gradio
EXPOSE 5000

# Comando por defecto
CMD ["python", "app.py"]

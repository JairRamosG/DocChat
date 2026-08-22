# Docker para DocChat - Guia Practica

## Por que Docker?

**El problema que resuelve:**

```
En tu computadora: funciona perfecto
En otra maquina: no funciona
En produccion: no funciona
```

**Por que pasa esto?**

- Diferentes versiones de Python
- Diferentes versiones de librerias
- Faltan archivos del sistema operativo
- Diferentes configuraciones del SO
- ChromaDB configurado diferente
- API keys no configuradas

**Docker solve esto:** Empaquetas TODO tu proyecto (codigo + dependencias + configuracion + ChromaDB) en una "caja" que funciona igual en cualquier lugar.

## Analogia simple

Piensa en Docker como una **caja de herramientas**:

```
Sin Docker:
  - Herramientas sueltas en tu taller
  - Cada vez que prestas una, cambian cosas
  - No sabes que version tienes

Con Docker:
  - Todo en una caja organizada
  - La caja es identica siempre
  - Puedes llevarla a cualquier lugar
```

## Los 3 conceptos clave

| Concepto | Que es | Ejemplo |
|----------|--------|---------|
| **Dockerfile** | Receta para crear la caja | "Ponle Python 3.11, instala LangChain, copia el codigo" |
| **Image** | La caja ya construida | "docchat:v1.0" |
| **Container** | Una copia de la caja funcionando | El proceso que corre tu app Gradio |

## Flujo de trabajo diario

### Paso 1: Crear el Dockerfile

```dockerfile
# Dockerfile

# Empezar con una imagen base de Python
FROM python:3.11-slim

# Definir directorio de trabajo
WORKDIR /app

# Copiar el archivo de dependencias
COPY requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el codigo
COPY . .

# Puerto de Gradio
EXPOSE 5000

# Comando para ejecutar
CMD ["python", "app.py"]
```

### Paso 2: Construir la imagen

```bash
# En la terminal, en la carpeta del proyecto
docker build -t docchat:v1.0 .
```

**Que hace esto?**
- Lee el Dockerfile
- Descarga la imagen base (python:3.11-slim)
- Ejecuta cada paso
- Crea una nueva imagen con todo instalado

### Paso 3: Ejecutar el container

```bash
# Ejecutar el container
docker run -p 5000:5000 docchat:v1.0
```

**Tu app ahora corre igual en:**
- Tu computadora
- La computadora de tu companero
- Un servidor en la nube
- Cualquier maquina con Docker

## Ejemplo real: DocChat

### Estructura del proyecto

```
DocChat/
├── Dockerfile
├── requirements.txt
├── app.py                    # Entry point - Gradio
├── agents/                   # Sistema multi-agente
│   ├── relevance_checker.py
│   ├── research_agent.py
│   ├── verification_agent.py
│   └── workflow.py
├── retriever/                # Busqueda hibrida
│   └── builder.py
├── document_processor/       # Procesamiento de documentos
│   └── file_handler.py
├── config/                   # Configuracion
│   ├── constants.py
│   └── settings.py
└── utils/
    └── logging.py
```

### Dockerfile para DocChat

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema (para librerias Python)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Primero copiar solo requirements.txt (para cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Luego copiar el codigo
COPY . .

# Puerto de Gradio
EXPOSE 5000

# Variables de entorno (se pasan en docker run)
# OPENROUTER_API_KEY - API key de OpenRouter

# Comando por defecto
CMD ["python", "app.py"]
```

### requirements.txt

```
gradio
langchain
langgraph
langchain-core
langchain-community
langchain-openrouter
langchain-openai
docling
chromadb
rank-bm25
langchain-text-splitters
pydantic-settings
python-dotenv
loguru
aiohttp
httpx
```

### Comandos que vas a usar todos los dias

```bash
# 1. Construir la imagen (despues de cambiar algo)
docker build -t docchat:v1.0 .

# 2. Ejecutar la app
docker run -p 5000:5000 \
  -e OPENROUTER_API_KEY=sk-tu-api-key \
  docchat:v1.0

# 3. Ejecutar con volumes (para persistir ChromaDB)
docker run -p 5000:5000 \
  -v docchat-chroma:/app/chroma_db \
  -v docchat-cache:/app/document_cache \
  -e OPENROUTER_API_KEY=sk-tu-api-key \
  docchat:v1.0

# 4. Ejecutar en modo interactivo (para debuggear)
docker run -it docchat:v1.0 /bin/bash

# 5. Ver containers corriendo
docker ps

# 6. Parar un container
docker stop <container_id>
```

## El problema de los volumes

**Sin volumes:** Cuando el container muere, ChromaDB y el cache de documentos se pierden.

**Con volumes:** Conectas volumes nombrados para persistir datos.

```bash
# Guardar ChromaDB y cache en volumes persistentes
docker run -p 5000:5000 \
  -v docchat-chroma:/app/chroma_db \
  -v docchat-cache:/app/document_cache \
  -e OPENROUTER_API_KEY=sk-tu-api-key \
  docchat:v1.0

# Ahora los datos sobreviven al reiniciar el container
```

## Docker Compose (cuando tienes multiples servicios)

Para DocChat con ChromaDB como servicio separado:

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - CHROMA_HOST=chroma
      - CHROMA_PORT=8000
    volumes:
      - docchat-cache:/app/document_cache
    depends_on:
      chroma:
        condition: service_healthy
    networks:
      - docchat-network

  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - docchat-chroma:/chroma/chroma
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - docchat-network

volumes:
  docchat-chroma:
  docchat-cache:

networks:
  docchat-network:
    driver: bridge
```

```bash
# Levantar todo
docker compose up

# Parar todo
docker compose down

# Levantar y reconstruir
docker compose up --build

# Ver logs
docker compose logs -f app
```

## Comandos esenciales del dia a dia

```bash
# Ver imagenes locales
docker images

# Ver containers corriendo
docker ps

# Ver logs de un container
docker logs <container_id>

# Entrar a un container que esta corriendo
docker exec -it <container_id> /bin/bash

# Eliminar containers muertos
docker container prune

# Eliminar imagenes que no usas
docker image prune -a
```

## Buenas practicas

1. **Usa .dockerignore** (igual que .gitignore)
```
.git
__pycache__
*.pyc
.env
chroma_db/
document_cache/
*.log
.pytest_cache
.venv
venv
```

2. **Ordena bien el Dockerfile** para aprovechar el cache
```dockerfile
# MAL: Copiar codigo primero
COPY . .
RUN pip install -r requirements.txt  # Se reinstala todo cada vez

# BIEN: Copiar requirements primero
COPY requirements.txt .
RUN pip install -r requirements.txt  # Solo se instala si cambia
COPY . .  # Este paso es rapido
```

3. **Usa imagenes slim** para reducir tamano
```dockerfile
# MAL (1GB)
FROM python:3.11

# BIEN (100MB)
FROM python:3.11-slim
```

4. **No ejecutes como root**
```dockerfile
# Agregar usuario no-root
RUN addgroup --system app && adduser --system --ingroup app app
USER app
```

5. **Usa health checks**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1
```

## Flujo completo resumido

```
1. Escribir codigo en tu maquina
2. Actualizar requirements.txt si necesitas
3. docker build -t docchat:v1.0 .
4. docker run -p 5000:5000 -e OPENROUTER_API_KEY=sk-xxx docchat:v1.0
5. Verificar que la app funciona
6. git push
7. En otro lugar: docker build + docker run = funciona igual
```

## Siguiente paso

Una vez que entiendas esto, pasamos a:
- **Docker Compose**: Orquestar app + ChromaDB
- **Tests**: Verificar que el container funciona correctamente
- **CI/CD**: Automatizar el build cada vez que haces push

# Bloque 1: Containerization con Docker

## Índice

1. [¿Qué es Containerization?](#1-qué-es-containerization)
2. [Virtual Machines vs Containers](#2-virtual-machines-vs-containers)
3. [Docker: El Estándar de la Industria](#3-docker-el-estándar-de-la-industria)
4. [Componentes Fundamentales](#4-componentes-fundamentales)
5. [El Dockerfile](#5-el-dockerfile)
6. [Imágenes y Capas](#6-imágenes-y-capas)
7. [Build Cache](#7-build-cache)
8. [Multi-Stage Builds](#8-multi-stage-builds)
9. [Networking en Docker](#9-networking-en-docker)
10. [Volumes y Persistencia](#10-volumes-y-persistencia)
11. [Variables de Entorno](#11-variables-de-entorno)
12. [Dockerignore](#12-dockerignore)
13. [Comandos Esenciales](#13-comandos-esenciales)
14. [Buenas Prácticas en Producción](#14-buenas-prácticas-en-producción)
15. [Seguridad](#15-seguridad)
16. [Optimización de Imágenes](#16-optimización-de-imágenes)
17. [Casos de Uso en la Industria](#17-casos-de-uso-en-la-industria)
18. [Errores Comunes y Cómo Evitarlos](#18-errores-comunes-y-cómo-evitarlos)
19. [Referencias](#19-referencias)

---

## 1. ¿Qué es Containerization?

Containerization es el proceso de empaquetar una aplicación y todas sus dependencias (librerías, configuraciones, archivos de sistema) en una unidad estandarizada llamada **container**. Esto garantiza que la aplicación se ejecute de manera consistente en cualquier entorno que soporte containers.

### El Problema que Resuelve

Antes de los containers, los desarrolladores enfrentaban el problema clásico: *"En mi máquina funciona"*. Una aplicación que funcionaba perfectamente en el desarrollo del programador fallaba en producción porque los entornos eran diferentes:

- Versión diferente de Python
- Librerías del sistema operativo diferentes
- Variables de entorno no configuradas
- Archivos de configuración distintos

Docker resuelve esto empaquetando **todo** en una imagen inmutable.

### Analogía Simple

Piensa en un container como una **casa móvil**:
- Tiene todo lo que necesita para vivir (dependencias)
- No depende de la infraestructura del terreno (entorno)
- Se puede mover de un lugar a otro sin cambios
- Varios containers pueden coexistir sin interferirse

---

## 2. Virtual Machines vs Containers

Es fundamental entender la diferencia porque son tecnologías complementarias, no rivales.

### Virtual Machines (VMs)

Una VM incluye una **copia completa del sistema operativo**:
```
┌─────────────────────┐
│   App A    App B    │
├─────────────────────┤
│   Bins/Libs         │
├─────────────────────┤
│   Guest OS          │  ← Cada VM tiene su propio SO
├─────────────────────┤
│   Hypervisor        │
├─────────────────────┤
│   Host OS           │
└─────────────────────┘
```

**Características:**
- Aislamiento completo (cada VM tiene su propio kernel)
- Pesada (gigabytes de tamaño)
- Lenta en arrancar (minutos)
- Uso intensivo de CPU y memoria
- Ideal para: diferentes sistemas operativos, aislamiento de seguridad crítico

### Containers

Un container comparte el **kernel del host**:
```
┌─────────────────────┐
│  Container A  │ Container B │
├─────────────────────┤
│  Bins/Libs   │ Bins/Libs   │
├─────────────────────┤
│  Docker Engine (compartido) │
├─────────────────────┤
│  Host OS + Kernel          │  ← Compartido entre todos
└─────────────────────┘
```

**Características:**
- Aislamiento a nivel de proceso (comparten kernel)
- Ligera (megabytes de tamaño)
- Rápida en arrancar (segundos)
- Uso eficiente de recursos
- Ideal para: microservicios, CI/CD, desarrollo local

### Comparación Directa

| Aspecto | VM | Container |
|---------|----| ----------|
| Tamaño | GB | MB |
| Arranque | Minutos | Segundos |
| SO | Completo | Compartido |
| Aislamiento | Fuerte (kernel propio) | Procesos |
| Overhead | Alto | Mínimo |
| Portabilidad | Limitada | Completa |
| Uso de memoria | Alto | Bajo |

### ¿Cuándo Usar Cada Uno?

**Usa VMs cuando:**
- Necesitas diferentes sistemas operativos
- Requieres aislamiento de seguridad absoluto
- Trabajas con aplicaciones legacy que requieren un SO completo

**Usa Containers cuando:**
- Quieres portabilidad y consistencia
- Necesitas despliegues rápidos
- Trabajas con microservicios
- Quieres optimizar recursos

---

## 3. Docker: El Estándar de la Industria

Docker es la plataforma más utilizada para containerization. No es el único (existen Podman, containerd, LXC), pero es el estándar de facto.

### Arquitectura de Docker

```
┌─────────────────────────────────────┐
│           Docker Client             │  ← CLI (docker build, docker run)
├─────────────────────────────────────┤
│          Docker Daemon              │  ← Servicio que gestiona containers
│  (dockerd)                          │
├─────────────────────────────────────┤
│     containerd    │    runc         │  ← Runtime de containers
├─────────────────────────────────────┤
│           Linux Kernel              │  ← Namespaces, cgroups
└─────────────────────────────────────┘
```

### Componentes del Ecosistema Docker

| Componente | Función |
|------------|---------|
| **Docker Engine** | El daemon que gestiona containers |
| **Docker CLI** | Interfaz de línea de comandos |
| **Docker Hub** | Registro público de imágenes |
| **Docker Compose** | Orquestación de múltiples containers |
| **Docker Desktop** | GUI + herramientas para desarrollo |
| **Docker Swarm** | Clustering nativo de Docker (menos usado ahora) |

---

## 4. Componentes Fundamentales

### Imagen (Image)

Una imagen es una **plantilla de solo lectura** que contiene:
- Sistema operativo base (generalmente Linux)
- Tiempo de ejecución (Python, Node.js, etc.)
- Librerías de la aplicación
- Código fuente
- Configuración
- Variables de entorno

Las imágenes son **inmutables**: una vez creadas, no se modifican.

### Container

Un container es una **instancia en ejecución** de una imagen:
- Tiene su propio sistema de archivos (capa de escritura)
- Puede leer y escribir datos
- Se puede iniciar, pausar, detener y eliminar
- Varios containers pueden ejecutarse desde la misma imagen

### Registry

Un registry es un **repositorio de imágenes**:
- **Docker Hub**: registro público (la opción por defecto)
- **AWS ECR**: Amazon Elastic Container Registry
- **GitHub GHCR**: GitHub Container Registry
- **Harbor**: registry self-hosted
- **Nexus**: registry empresarial

### Tag

Un tag es una **etiqueta** que identifica una versión de imagen:
```
python:3.11-slim
├──┬──── ──┬─ ──┬
│  │       │    │
│  │       │    └── Variante (slim, alpine, bullseye)
│  │       └─────── Versión
│  └─────────────── Nombre del repositorio
└────────────────── Organización (opcional: myorg/python)
```

---

## 5. El Dockerfile

Un Dockerfile es un **archivo de texto con instrucciones** para construir una imagen.

### Estructura Básica

```dockerfile
# Instrucción: Comentario de qué hace este paso
INSTRUCCIÓN argumentos
```

### Instrucciones Principales

#### FROM - Imagen base

```dockerfile
# Formato completo
FROM imagen:tag AS nombre

# Ejemplos
FROM python:3.11-slim
FROM node:20-alpine AS builder
FROM gcr.io/distroless/python3-debian12
```

**Variantes comunes:**
- `slim`: mínima, solo lo esencial
- `alpine`: basada en Alpine Linux (mínima pero con musl libc)
- `distroless`: sin shell, máxima seguridad
- `bullseye/bookworm`: Debian completa

#### WORKDIR - Directorio de trabajo

```dockerfile
# Crea el directorio si no existe y cambia a él
WORKDIR /app

# Equivale a:
# RUN mkdir -p /app
# WORKDIR /app
```

#### COPY vs ADD - Copiar archivos

```dockerfile
# COPY: copia archivos simples (PREFERIR SIEMPRE)
COPY requirements.txt .
COPY src/ ./src/

# ADD: copia + extrae tarballs + soporta URLs (EVITAR)
ADD archive.tar.gz /app/
ADD https://example.com/file.txt /app/
```

**Regla:** Usa `COPY` a menos que necesites la funcionalidad extra de `ADD`.

#### RUN - Ejecutar comandos

```dockerfile
# Forma shell (ejecuta en /bin/sh -c)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Forma exec (sin shell, más seguro)
RUN ["pip", "install", "-r", "requirements.txt"]
```

**Optimización:** Combina comandos `RUN` para reducir capas:
```dockerfile
# MAL (múltiples capas)
RUN apt-get update
RUN apt-get install -y gcc
RUN rm -rf /var/lib/apt/lists/*

# BIEN (una capa)
RUN apt-get update && \
    apt-get install -y gcc && \
    rm -rf /var/lib/apt/lists/*
```

#### ENV - Variables de entorno

```dockerfile
# Definir variable
ENV APP_ENV=production
ENV PYTHONUNBUFFERED=1

# Múltiples variables
ENV APP_HOME=/app \
    APP_PORT=5000
```

#### EXPOSE - Documentar puertos

```dockerfile
# Solo documenta, NO publica el puerto
EXPOSE 5000

# Para publicar, usar: docker run -p 5000:5000
```

#### CMD vs ENTRYPOINT - Comando inicial

```dockerfile
# CMD: comando por defecto (se puede sobreescribir)
CMD ["python", "app.py"]
CMD python app.py

# ENTRYPOINT: comando que siempre se ejecuta
ENTRYPOINT ["python"]
CMD ["app.py"]

# Combinación:
# ENTRYPOINT define el ejecutable
# CMD define los argumentos por defecto
```

#### USER - Usuario de ejecución

```dockerfile
# Por defecto ejecuta como root (MALA PRÁCTICA)
RUN addgroup --system app && \
    adduser --system --ingroup app app
USER app
```

**¿Por qué no ejecutar como root?** Si un atacante compromete el container, tendrá permisos de root dentro del container, lo cual facilita la escalada de privilegios.

---

## 6. Imágenes y Capas

### Sistema de Capas (Layers)

Cada instrucción en un Dockerfile crea una **capa**:
```
Capa 5: COPY src/ ./src/          (15 MB)
Capa 4: RUN pip install deps      (200 MB)
Capa 3: COPY requirements.txt     (1 KB)
Capa 2: WORKDIR /app              (0 MB)
Capa 1: python:3.11-slim          (120 MB)
```

### Por Qué Importan las Capas

1. **Cache**: si una capa no cambia, se reutiliza en builds futuros
2. **Tamaño**: cada capa contribuye al tamaño total
3. **Reutilización**: múltiples imágenes pueden compartir capas
4. **Registry**: se suben/downloaded por capas

### Inspeccionar Capas

```bash
# Ver las capas de una imagen
docker history python:3.11-slim

# Ver el tamaño de cada capa
docker images python:3.11-slim
```

### Multi-Stage Builds y Capas

En multi-stage builds, solo las capas del stage final se incluyen en la imagen final:
```dockerfile
FROM node:20 AS builder
# ... muchas capas de build ...
COPY . .
RUN npm run build  # 500MB de node_modules

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html  # Solo los archivos estáticos
# Resultado: imagen de ~20MB, no de ~500MB
```

---

## 7. Build Cache

Docker utiliza un **sistema de cache** para acelerar builds.

### Cómo Funciona

```
# Dockerfile
FROM python:3.11-slim           # ← Checkea cache
WORKDIR /app                    # ← Checkea cache
COPY requirements.txt .         # ← Checkea cache
RUN pip install -r requirements.txt  # ← Si requirements.txt no cambió, usa cache
COPY . .                        # ← Si algo anterior cambió, rebuild desde aquí
```

### Reglas de Cache

1. **Primera vez**: todo se ejecuta (sin cache)
2. **Segunda vez**: Docker verifica si cada capa cambió
3. **Si una capa cambia**: todas las posteriores se reconstruyen
4. **El contexto de build** afecta la cache (archivos enviados al daemon)

### El Problema de `COPY . .`

```dockerfile
# MALA PRÁCTICA
COPY . .  # ← Esto invalida el cache de TODAS las capas siguientes
RUN pip install -r requirements.txt  # ← Se ejecuta siempre

# BUENA PRÁCTICA
COPY requirements.txt .  # ← Solo invalida si requirements.txt cambió
RUN pip install -r requirements.txt
COPY . .  # ← Las capas anteriores se cachean
```

### BuildKit y Cache Avanzado

BuildKit (el builder moderno de Docker) soporta cache más avanzado:
```dockerfile
# syntax=docker/dockerfile:1

# Cache mounts para pip
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Cache mounts para apt
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && apt-get install -y gcc
```

---

## 8. Multi-Stage Builds

Multi-stage builds permiten **dividir el proceso de build en etapas** para reducir el tamaño de la imagen final.

### El Problema

Una imagen de Node.js para compilar React puede tener 1GB+:
```
node_modules: 500MB
dev dependencies: 200MB
source code: 10MB
Total: ~710MB
```

Pero en producción solo necesitas los archivos estáticos (~10MB).

### La Solución

```dockerfile
# Stage 1: Builder
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Production
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# Solo copia los archivos compilados, sin node_modules
```

### Ejemplo para Python

```dockerfile
# Stage 1: Builder (compila dependencias)
FROM python:3.11-slim AS builder
WORKDIR /app
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime (solo lo necesario)
FROM python:3.11-slim
WORKDIR /app

# Copiar dependencias del builder
COPY --from=builder /root/.local /root/.local

# Copiar código
COPY . .

# Configurar PATH
ENV PATH=/root/.local/bin:$PATH

CMD ["python", "app.py"]
```

### Beneficios

| Aspecto | Sin Multi-Stage | Con Multi-Stage |
|---------|-----------------|-----------------|
| Tamaño imagen | 1GB+ | 100MB |
| Tiempo de build | Lento | Más rápido |
| Seguridad | Más superficie de ataque | Menos herramientas |
| Cache | Menos eficiente | Más eficiente |

---

## 9. Networking en Docker

### Tipos de Red

#### bridge (por defecto)

```bash
# Red bridge por defecto
docker network ls

# Containers en la misma red se comunican por nombre
docker run --name app --network bridge myapp
docker run --name db --network bridge postgres
# app puede acceder a db en: postgres:5432
```

#### host

```bash
# Comparte la red del host (Linux)
docker run --network host myapp
# La app escucha en el puerto del host directamente
```

#### none

```bash
# Sin acceso a red
docker run --network none myapp
# Útil para seguridad máxima
```

#### user-defined (recomendado)

```bash
# Crear red personalizada
docker network create docchat-network

# Usar la red
docker run --name chroma --network docchat-network chromadb
docker run --name app --network docchat-network docchat

# Se comunican por nombre: chroma:8000
```

### Comunicación entre Containers

```bash
# Desde app, acceder a chroma:
# http://chroma:8000 (si están en la misma red)

# Verificar conectividad
docker exec app ping chroma
docker exec app curl http://chroma:8000/api/v1/heartbeat
```

### Exponer Puertos

```bash
# -p host_port:container_port
docker run -p 5000:5000 myapp

# -p host_port:container_port/protocol
docker run -p 8080:80/tcp myapp

# -P (exponer todos los puertos documentados con EXPOSE)
docker run -P myapp

# Rango de puertos
docker run -p 5000-5010:5000-5010 myapp
```

---

## 10. Volumes y Persistencia

### El Problema

Los containers son **efímeros**: cuando se eliminan, todos los datos escritos dentro se pierden.

### Tipos de Persistencia

#### 1. Volumes (Recomendado)

```bash
# Crear volume nombrado
docker volume create docchat-data

# Usar el volume
docker run -v docchat-data:/app/data myapp

# Listar volumes
docker volume ls

# Inspeccionar volume
docker volume inspect docchat-data
```

**Ventajas:**
- Gestionados por Docker
- Backup más fácil
- Funcionan en Linux y Mac
- Mejor rendimiento

#### 2. Bind Mounts

```bash
# Montar directorio del host
docker run -v /home/user/project:/app myapp

# Con opciones
docker run -v /home/user/project:/app:ro myapp  # Solo lectura
docker run -v /home/user/project:/app:rw myapp  # Lectura/escritura
```

**Ventajas:**
- Desarrollo: ver cambios en tiempo real
- Acceso directo desde el host

**Desventajas:**
- Depende de la estructura del host
- Problemas de permisos entre host y container

#### 3. tmpfs Mounts

```bash
# Montar en memoria (se pierde al detener)
docker run --tmpfs /app/temp myapp
```

**Uso:** Archivos temporales que no deben persistir.

### Persistencia en DocChat

```bash
# ChromaDB necesita persistir datos
docker run -v docchat-chroma:/chroma/chroma myapp

# Cache de documentos procesados
docker run -v docchat-cache:/app/document_cache myapp

# Combinar volumes
docker run \
  -v docchat-chroma:/chroma/chroma \
  -v docchat-cache:/app/document_cache \
  myapp
```

---

## 11. Variables de Entorno

### Definir en Dockerfile

```dockerfile
ENV APP_ENV=production
ENV PYTHONUNBUFFERED=1
ENV CHROMA_HOST=chroma
ENV CHROMA_PORT=8000
```

### Sobreescribir en docker run

```bash
# Una variable
docker run -e APP_ENV=development myapp

# Múltiples variables
docker run \
  -e APP_ENV=development \
  -e CHROMA_HOST=localhost \
  myapp

# Desde archivo .env
docker run --env-file .env myapp
```

### Archivo .env

```bash
# .env
APP_ENV=production
OPENROUTER_API_KEY=sk-xxx
CHROMA_HOST=chroma
CHROMA_PORT=8000
```

### Mejores Prácticas

1. **Nunca hardcodear secrets** en el Dockerfile
2. **Usar .env** para desarrollo local
3. **Usar secrets de Docker/Kubernetes** en producción
4. **Documentar** las variables requeridas en el README
5. **Validar** que las variables existan al inicio de la app

---

## 12. Dockerignore

Un archivo `.dockerignore` excluye archivos del **contexto de build**.

### Por Qué Importar

Sin `.dockerignore`, Docker envía **todo** el directorio al daemon, incluyendo:
- `.git/` (puede ser enorme)
- `node_modules/` (innecesarios en Python)
- `__pycache__/`
- `.env` (puede contener secrets)
- `*.pyc`
- `.venv/`
- `chroma_db/` (datos de prueba)

### Ejemplo para DocChat

```
# .dockerignore
.git
.gitignore
.env
*.pyc
__pycache__
.pytest_cache
.venv
venv
env
chroma_db
document_cache
*.log
README.md
producción.md
bloque1-docker.md
tests/
```

### Beneficios

| Sin .dockerignore | Con .dockerignore |
|-------------------|-------------------|
| Contexto de build: 500MB | Contexto de build: 5MB |
| Build lento | Build rápido |
| Cache inválida frecuentemente | Cache más estable |
| Riesgo de exponer secrets | Secrets excluidos |

---

## 13. Comandos Esenciales

### Gestión de Imágenes

```bash
# Construir imagen
docker build -t nombre:tag .
docker build -t docchat:latest -f Dockerfile.prod .

# Listar imágenes
docker images
docker images -a  # Incluir imágenes intermedias

# Eliminar imagen
docker rmi imagen:tag
docker image prune  # Eliminar imágenes sin usar

# Inspeccionar imagen
docker history imagen:tag
docker inspect imagen:tag

# Buscar imagen
docker search python
```

### Gestión de Containers

```bash
# Ejecutar container
docker run -d -p 5000:5000 --name docchat docchat:latest
# -d: detached mode (background)
# -p: publicar puerto
# --name: nombre del container

# Listar containers
docker ps  # Containers activos
docker ps -a  # Todos los containers

# Detener container
docker stop docchat
docker stop $(docker ps -q)  # Detener todos

# Eliminar container
docker rm docchat
docker rm $(docker ps -aq)  # Eliminar todos

# Ejecutar comando en container
docker exec -it docchat bash
docker exec docchat python --version

# Ver logs
docker logs docchat
docker logs -f docchat  # Seguir logs en tiempo real
docker logs --tail 100 docchat  # Últimas 100 líneas
```

### Gestión de Volumes

```bash
# Crear volume
docker volume create mydata

# Listar volumes
docker volume ls

# Eliminar volume
docker volume rm mydata
docker volume prune  # Eliminar volumes sin usar

# Inspeccionar
docker volume inspect mydata
```

### Limpieza

```bash
# Eliminar todo lo que no se esté usando
docker system prune

# Eliminar todo (incluyendo volumes)
docker system prune -a --volumes

# Ver espacio utilizado
docker system df
```

---

## 14. Buenas Prácticas en Producción

### 1. Usa Imágenes Oficiales y Verified

```dockerfile
# BIEN: imagen oficial
FROM python:3.11-slim

# EVITAR: imágenes no verificadas
FROM randomuser/python
```

### 2. Fija Versiones Específicas

```dockerfile
# BIEN: versión específica
FROM python:3.11.9-slim

# EVITAR: latest
FROM python:latest
```

### 3. Usa Multi-Stage Builds

```dockerfile
# BIEN: separar build de runtime
FROM python:3.11-slim AS builder
# ... build ...

FROM python:3.11-slim
COPY --from=builder /app /app
```

### 4. No Ejecutes como Root

```dockerfile
# BIEN: usuario no-root
RUN addgroup --system app && adduser --system --ingroup app app
USER app
```

### 5. Ordena las Capas por Frecuencia de Cambio

```dockerfile
# Cambios frecuentes al final
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .     # ← Cambia raramente
RUN pip install -r requirements.txt
COPY . .                     # ← Cambia frecuentemente
```

### 6. Limpia Archivos Temporales

```dockerfile
RUN apt-get update && \
    apt-get install -y gcc && \
    rm -rf /var/lib/apt/lists/*  # ← Limpiar cache
```

### 7. Usa HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1
```

### 8. Documenta Puertos y Volumes

```dockerfile
EXPOSE 5000
VOLUME ["/app/data"]
```

---

## 15. Seguridad

### Principios de Seguridad

1. **Principio de mínimo privilegio**: ejecutar con menos permisos posibles
2. **Imágenes mínimas**: menos herramientas = menos superficie de ataque
3. **No secrets en imágenes**: usar variables de entorno o secrets managers
4. **Escaneo de vulnerabilidades**: usar herramientas como Trivy, Snyk

### Escaneo de Vulnerabilidades

```bash
# Con Trivy
trivy image docchat:latest

# Con Docker Scout
docker scout cves docchat:latest

# Con Snyk
snyk container test docchat:latest
```

### .dockerignore para Seguridad

```
# Excluir secrets
.env
*.key
*.pem
credentials*
secrets*
```

### Imágenes Distroless

Para máxima seguridad, usa imágenes distroless:
```dockerfile
FROM gcr.io/distroless/python3-debian12
COPY --from=builder /app /app
CMD ["app.py"]
```

**Ventajas:** No hay shell, no hay package manager, no hay utils. Un atacante no tiene herramientas para explotar.

### Best Practices de Seguridad

| Práctica | Por Qué |
|----------|---------|
| No ejecutar como root | Previne escalada de privilegios |
| No instalar herramientas innecesarias | Reduce superficie de ataque |
| Escanear imágenes | Detectar vulnerabilidades conocidas |
| Usar .dockerignore | Evitar exponer secrets |
| Fijar versiones | Reproducibilidad y seguridad |
| Usar HEALTHCHECK | Detectar containers comprometidos |

---

## 16. Optimización de Imágenes

### Reducir Tamaño

**1. Elige la imagen base correcta:**
```dockerfile
# ~900MB
FROM python:3.11

# ~120MB
FROM python:3.11-slim

# ~50MB
FROM python:3.11-alpine

# ~30MB
FROM gcr.io/distroless/python3-debian12
```

**2. Usa multi-stage builds:**
```dockerfile
FROM python:3.11-slim AS builder
RUN pip install --user -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /root/.local /root/.local
```

**3. Limpia cache:**
```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

**4. Combina RUNs:**
```dockerfile
RUN apt-get update && \
    apt-get install -y gcc && \
    rm -rf /var/lib/apt/lists/*
```

### Reducir Tiempo de Build

**1. Usa BuildKit:**
```bash
DOCKER_BUILDKIT=1 docker build .
```

**2. Ordena por frecuencia de cambio:**
```dockerfile
COPY requirements.txt .  # Raramente cambia
RUN pip install -r requirements.txt
COPY . .  # Cambia frecuentemente
```

**3. Usa cache mounts:**
```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

### Medir Impacto

```bash
# Ver tamaño de imagen
docker images docchat:latest

# Ver detalle de capas
docker history docchat:latest

# Inspeccionar tamaño por capa
docker inspect docchat:latest
```

---

## 17. Casos de Uso en la Industria

### 1. Microservicios

Cada servicio en su propio container:
```
┌─────────┐ ┌─────────┐ ┌─────────┐
│  Auth   │ │  API    │ │  Worker │
└─────────┘ └─────────┘ └─────────┘
     ↓           ↓           ↓
  Redis      PostgreSQL   RabbitMQ
```

**Empresas:** Netflix, Uber, Spotify

### 2. CI/CD

Containers para builds reproducibles:
```yaml
# GitHub Actions
jobs:
  test:
    runs-on: ubuntu-latest
    container: python:3.11-slim
    steps:
      - run: pytest tests/
```

**Beneficios:** Entorno consistente, aislamiento, cleanup automático.

### 3. Desarrollo Local

Docker Compose para entornos de desarrollo:
```yaml
services:
  app:
    build: .
    volumes:
      - .:/app  # Hot reload
  db:
    image: postgres:16
```

**Beneficios:** Setup en minutos, entorno idéntico al de producción.

### 4. Machine Learning

Containers para modelos ML:
```dockerfile
FROM python:3.11-slim
RUN pip install torch transformers
COPY model/ /app/model
CMD ["python", "serve.py"]
```

**Empresas:** Google, Amazon, Microsoft

### 5. edge Computing

Containers en dispositivos IoT:
```bash
# Docker en Raspberry Pi
docker run -d --restart=always myapp
```

**Beneficios:** Despliegue remoto, actualizaciones fáciles.

---

## 18. Errores Comunes y Cómo Evitarlos

### 1. No Usar .dockerignore

**Problema:** El build es lento, el contexto es enorme.

**Solución:** Crear `.dockerignore` desde el inicio.

### 2. Múltiples RUNs Innecesarios

**Problema:** Imagen grande, build lento.

```dockerfile
# MAL
RUN apt-get update
RUN apt-get install -y gcc
RUN pip install -r requirements.txt

# BIEN
RUN apt-get update && \
    apt-get install -y gcc && \
    rm -rf /var/lib/apt/lists/*
```

### 3. Copiar Todo al Inicio

**Problema:** Cache se invalida frecuentemente.

```dockerfile
# MAL
COPY . .
RUN pip install -r requirements.txt

# BIEN
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
```

### 4. Ejecutar como Root

**Problema:** Riesgo de seguridad.

```dockerfile
# MAL
CMD ["python", "app.py"]  # Ejecuta como root

# BIEN
RUN addgroup --system app && adduser --system --ingroup app app
USER app
CMD ["python", "app.py"]
```

### 5. No Usar HEALTHCHECK

**Problema:** Docker no sabe si la app está funcionando.

```dockerfile
# Agregar health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:5000/ || exit 1
```

### 6. Hardcodear Secrets

**Problema:** Secrets en la imagen, visible para cualquiera.

```dockerfile
# MAL
ENV API_KEY=sk-abc123

# BIEN
# Pasar en docker run: -e API_KEY=sk-abc123
```

### 7. No Limpiar Cache de Package Manager

**Problema:** Imagen más grande de lo necesario.

```dockerfile
# MAL
RUN apt-get update && apt-get install -y gcc

# BIEN
RUN apt-get update && \
    apt-get install -y gcc && \
    rm -rf /var/lib/apt/lists/*
```

---

## 19. Referencias

### Documentación Oficial
- [Docker Documentation](https://docs.docker.com/)
- [Dockerfile Reference](https://docs.docker.com/engine/reference/builder/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)

### Herramientas
- [Trivy](https://github.com/aquasecurity/trivy) - Escaneo de vulnerabilidades
- [Hadolint](https://github.com/hadolint/hadolint) - Linter para Dockerfiles
- [Dive](https://github.com/wagoodman/dive) - Explorar capas de imágenes
- [BuildKit](https://github.com/moby/buildkit) - Builder avanzado

### Recursos de Aprendizaje
- [Docker Curriculum](https://docker-curriculum.com/)
- [Play with Docker](https://labs.play-with-docker.com/)
- [Docker Academy](https://academy.docker.com/)

---

## Apéndice: Comandos Rápidos de Referencia

```bash
# Build
docker build -t name:tag .
docker build -t name:tag -f Dockerfile.prod .

# Run
docker run -d -p 5000:5000 --name app name:tag
docker run -it --rm name:tag bash
docker run --env-file .env name:tag

#_PS
docker ps
docker ps -a
docker ps -q

# Logs
docker logs app
docker logs -f app
docker logs --tail 100 app

# Exec
docker exec -it app bash
docker exec app python script.py

# Stop/Remove
docker stop app
docker rm app
docker rm -f app

# Cleanup
docker system prune
docker system prune -a --volumes
docker volume prune

# Inspect
docker inspect app
docker inspect app --format '{{.NetworkSettings.IPAddress}}'
docker stats
```

---

*Última actualización: Agosto 2026*

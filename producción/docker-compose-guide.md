# Docker Compose para DocChat - Guia Practica

## Por que Docker Compose?

**El problema que resuelve:**

```
Tu proyecto necesita 2 cosas:
  1. App Python (Gradio)
  2. ChromaDB (base de datos vectorial)

Sin Docker Compose:
  - Tienes que ejecutar 2 comandos separados
  - Tienes que crear redes manualmente
  - Tienes que coordinar el orden
  - Si algo falla, es un desastre arreglarlo
```

**Docker Compose resolve esto:** Defines todo en UN ARCHIVO y ejecutas UN SOLO COMANDO.

## Analogia simple

Piensa en Docker Compose como un **director de orquesta**:

```
Sin Compose:
  - Tocas el violin Y el piano Y la bateria al mismo tiempo
  - Nadie coordina
  - Suena un desastre

Con Compose:
  - Un director dice quien toca que y cuando
  - Todo suena en armonia
  - Si algo falla, el director avisa
```

## La diferencia clave

| Sin Compose | Con Compose |
|-------------|-------------|
| Varios comandos `docker run` | Un solo `docker compose up` |
| Redes manuales | Compose las crea |
| Volumes manuales | En el archivo |
| Orden manual | Compose coordina |
| Parar todo: varios `docker stop` | Un solo `docker compose down` |

## Cuando necesitas Docker Compose

**Usa Compose cuando tu proyecto tiene:**
- Mas de 1 servicio (app + base de datos)
- Base de datos separada (PostgreSQL, MySQL, Redis, ChromaDB)
- Cache separado (Redis, Memcached)
- Workers separados (colas de mensajes)

**No necesitas Compose cuando:**
- Solo tienes 1 container
- Es un proyecto muy simple
- Solo quieres probar algo rapido

## Estructura basica de un docker-compose.yml

```yaml
# docker-compose.yml

version: '3.8'    # Version de Docker Compose

services:         # Aqui defines tus servicios (containers)
  
  app:            # Nombre del servicio 1
    build: .      # Construir desde el Dockerfile actual
    ports:
      - "5000:5000"    # Puerto: host:container
    environment:
      - CHROMA_HOST=chroma   # Variable de entorno
    depends_on:
      - chroma      # Esperar a que chroma este listo

  chroma:          # Nombre del servicio 2
    image: chromadb/chroma:latest   # Usar imagen pre-hecha
    ports:
      - "8000:8000"
    volumes:
      - docchat-chroma:/chroma/chroma   # Persistir datos

volumes:          # Definir volumes para persistir datos
  docchat-chroma:
```

## Los elementos explicados

### version: '3.8'
La version del formato del archivo. Usa la 3.8 que es estable.

### services:
Aqui defines cada container que necesitas. Cada servicio es un container.

```yaml
services:
  app:        # Container 1: Tu app Python
  chroma:     # Container 2: ChromaDB
  redis:      # Container 3 (si lo necesitaras)
```

### build: .
Le dice a Docker: "Construye la imagen desde el Dockerfile que esta en esta carpeta".

```yaml
app:
  build: .    # Busca Dockerfile en la carpeta actual
```

### image:
Usa una imagen pre-hecha de Docker Hub.

```yaml
chroma:
  image: chromadb/chroma:latest   # No necesita Dockerfile
```

### ports:
Mapea puertos del host al container.

```yaml
ports:
  - "5000:5000"    # host:container
  - "8000:8000"
```

### environment:
Variables de entorno para el container.

```yaml
environment:
  - CHROMA_HOST=chroma        # La app se conecta a "chroma"
  - OPENROUTER_API_KEY=sk-xxx
```

### depends_on:
Define que servicios deben estar listos antes de que este inicie.

```yaml
app:
  depends_on:
    - chroma    # ChromaDB debe estar listo antes que la app
```

### volumes:
Persiste datos mas alla de la vida del container.

```yaml
volumes:
  - docchat-chroma:/chroma/chroma
  # Nombre del volume : ruta dentro del container
```

## Flujo de trabajo diario

### Paso 1: Crear el docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - CHROMA_HOST=chroma
    depends_on:
      - chroma

  chroma:
    image: chromadb/chroma:latest
    ports:
      - "8000:8000"
    volumes:
      - docchat-chroma:/chroma/chroma

volumes:
  docchat-chroma:
```

### Paso 2: Levantar todo

```bash
# Ejecutar en la carpeta del proyecto
docker compose up
```

Esto hace:
1. Construye la imagen de tu app (si hay Dockerfile)
2. Descarga la imagen de ChromaDB
3. Crea una red para que se comuniquen
4. Crea el volume para persistir datos
5. Ejecuta ambos containers

### Paso 3: Verificar

```bash
# Ver containers corriendo
docker compose ps

# Ver logs
docker compose logs

# Ver logs de un servicio especifico
docker compose logs app
docker compose logs chroma
```

### Paso 4: Parar todo

```bash
docker compose down
```

Esto para y elimina todos los containers, pero NO borra los volumes (tus datos se mantienen).

## Comandos esenciales

```bash
# Levantar todo (background)
docker compose up -d

# Ver estado
docker compose ps

# Ver logs (tiempo real)
docker compose logs -f

# Parar (sin borrar datos)
docker compose down

# Parar y borrar TODO (incluyendo volumes)
docker compose down -v

# Reconstruir si cambió el Dockerfile
docker compose up --build

# Ver el log de un servicio
docker compose logs -f app
```

## Ejemplo real: DocChat con ChromaDB

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
    restart: unless-stopped

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
    restart: unless-stopped

volumes:
  docchat-chroma:
  docchat-cache:

networks:
  docchat-network:
    driver: bridge
```

## Explicacion de este ejemplo

### healthcheck
Verifica que ChromaDB esta realmente listo antes de que la app se conecte.

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
  interval: 10s      # Cada 10 segundos verificar
  timeout: 5s        # Si no responde en 5 segundos, falla
  retries: 5         # Intentar 5 veces antes de declarar falla
```

### condition: service_healthy
Espera a que el healthcheck pase antes de iniciar el siguiente servicio.

```yaml
depends_on:
  chroma:
    condition: service_healthy    # Esperar a que ChromaDB este healthy
```

### restart: unless-stopped
Si el container falla, reiniciarlo automaticamente.

### networks
Crea una red privada para que los servicios se comuniquen por nombre.

```yaml
networks:
  docchat-network:
    driver: bridge
```

Dentro de esta red, la app puede conectarse a ChromaDB usando "chroma" como hostname.

## Variables de entorno con .env

En vez de escribir API keys en el archivo, usa un archivo .env:

```bash
# .env
OPENROUTER_API_KEY=sk-tu-api-key
```

```yaml
# docker-compose.yml
services:
  app:
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
```

Docker Compose lee automaticamente el archivo .env.

## Buenas practicas

1. **Nunca subas el .env a Git**
```
# .gitignore
.env
```

2. **Usa healthcheck para servicios criticos**
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/"]
  interval: 30s
  timeout: 10s
  retries: 3
```

3. **Define volumes para datos persistentes**
```yaml
volumes:
  - mydata:/data    # Los datos sobreviven a 'docker compose down'
```

4. **Usa restart para servicios importantes**
```yaml
restart: unless-stopped    # Reiniciar si falla
```

5. **Nunca hardcodes API keys**
```yaml
# MAL
environment:
  - API_KEY=sk-abc123

# BIEN
environment:
  - API_KEY=${API_KEY}
```

## Errores comunes

### "No such service: app"
Verifica que el nombre del servicio coincida con lo que pones en depends_on.

### "Port already in use"
Algo mas esta usando ese puerto. Cambia el puerto o para el otro servicio.

### "Container failed to start"
Ver logs: `docker compose logs app`

### "ChromaDB not ready"
Agrega healthcheck y depends_on con condition.

## Flujo completo resumido

```
1. Crear docker-compose.yml con tus servicios
2. docker compose up -d
3. Verificar: docker compose ps
4. Probar: http://localhost:5000
5. Ver logs: docker compose logs -f
6. Parar: docker compose down
```

## Siguiente paso

Una vez que entiendas Compose, pasamos a:
- **Tests**: Verificar que todo funciona correctamente
- **CI/CD**: Automatizar builds y deploys
- **AWS**: Desplegar en la nube

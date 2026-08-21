# Notas de Producción: DocChat

## Mi Objetivo

Aprender a llevar DocChat de una aplicación local a un sistema robusto, testeado y desplegado en producción. Cada bloque es un módulo de aprendizaje que implementaré secuencialmente, documentando lo que aprendo para futuro referencia.

---

## Arquitectura que voy a construir

```
GitHub Actions (CI/CD)
    ↓
AWS EC2 + CloudFormation
    ↓
Docker Compose
    ├── App Python (Gradio)
    └── ChromaDB (vector store)
    ↓
Caddy (HTTPS + proxy reverso)
    ↓
Internet → Usuario
```

**Decisión técnica:** Uso ChromaDB como vector store en lugar de PostgreSQL. Esto simplifica la infraestructura pero implica consideraciones específicas sobre persistencia y escalabilidad que documentaré en cada bloque.

**Herramienta de testing elegida:** pytest. Es el estándar en el ecosistema Python, flexible, con plugins útiles y buena integración con Docker Compose para tests de integración.

---

## Bloques de Aprendizaje

### Bloque 1: Containerization con Docker

**Objetivo:** Empaquetar DocChat en un contenedor reproducible que funcione idéntico en cualquier máquina.

**Conceptos clave:**
- Qué es un Dockerfile y cómo funciona el build cache
- Multi-stage builds: compilar dependencias vs runtime final
- Persistencia de datos con Docker volumes
- Networking entre containers
- Imágenes base: por qué elegir `python:3.11-slim` sobre `python:3.11`

**Aplicación a DocChat:**
- Crear Dockerfile que instale dependencias de `requirements.txt`
- Manejar la cache de ChromaDB (`chroma_db/` directory)
- Manejar el cache de documentos procesados (`document_cache/`)
- Exponer el puerto de Gradio (5000)
- Configurar variables de entorno (API keys)

**Resultado esperado:**
```bash
docker build -t docchat:latest .
docker run --rm -p 5000:5000 -v docchat-data:/app/data docchat:latest
# App funcionando en localhost:5000 con persistencia
```

**Conceptos que debo dominar:**
- Diferencia entre imagen y container
- Para qué sirven los multi-stage builds
- Cómo persistir datos cuando el container se destruye
- Qué es el build cache y cómo afecta el tiempo de build

---

### Bloque 2: Docker Compose y Orquestación

**Objetivo:** Definir y orquestar múltiples servicios (App + ChromaDB) con un solo comando.

**Conceptos clave:**
- Estructura de un `docker-compose.yaml`
- Servicios, redes y volúmenes
- Health checks: cómo verificar que un servicio está listo
- Dependencias entre servicios (`depends_on`)
- Variables de entorno compartidas
- Profiles para ambientes (dev vs prod)

**Aplicación a DocChat:**
- Definir servicio `app` (Python/Gradio)
- Definir servicio `chroma` (ChromaDB server)
- Configurar red interna para que la app se conecte a Chroma
- Volume compartido para persistencia de ChromaDB
- Health check para ChromaDB antes de levantar la app

**Resultado esperado:**
```bash
docker compose up --build
# Ambos servicios levantados y comunicándose
# ChromaDB accesible internamente en chroma:8000
# App accesible en localhost:5000
```

**Conceptos que debo dominar:**
- Diferencia entre Docker Compose y Kubernetes
- Qué es un health check y por qué es importante
- Cómo manejar servicios que dependen de otros
- Diferencia entre `docker run` y `docker compose up`

---

### Bloque 3: Testing con pytest

**Objetivo:** Crear una pirámide de tests que garantice que los cambios no rompen funcionalidad existente.

**Herramienta elegida:** pytest

**Conceptos clave:**
- Pirámide de testing: unit → integration → E2E
- Unit tests: tests aislados de funciones puras
- Integration tests: tests contra servicios reales (Docker Compose)
- E2E tests: tests que simulan el flujo completo del usuario
- Mocking: cuándo mockear vs cuándo testear real
- Test fixtures: datos de prueba reproducibles
- Cobertura de código: métricas útiles vs métricas vanidosas
- Markers de pytest: `@pytest.mark.integration`, `@pytest.mark.slow`

**Aplicación a DocChat:**
- **Unit tests:** testear funciones de `DocumentProcessor`, parsing, chunking
- **Integration tests:** testear el pipeline completo (upload → retrieve → answer)
- **E2E tests:** simular usuario subiendo PDF y recibiendo respuesta
- **Tests del retriever:** verificar que BM25 + ChromaDB funcionan juntos
- **Tests de agentes:** verificar que RelevanceChecker, ResearchAgent, VerificationAgent responden correctamente

**Estructura de tests:**
```
tests/
├── unit/
│   ├── test_document_processor.py
│   ├── test_retriever.py
│   └── test_agents.py
├── integration/
│   ├── test_pipeline.py
│   └── test_retriever_chroma.py
├── e2e/
│   └── test_full_flow.py
├── conftest.py          # Fixtures compartidos
└── pytest.ini           # Configuración
```

**Plugins de pytest que voy a usar:**
- `pytest-asyncio` para operaciones asíncronas
- `pytest-cov` para cobertura de código
- `pytest-docker` para tests contra Docker Compose

**Resultado esperado:**
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests (requiere docker compose)
pytest tests/integration/ -v

# E2E tests
pytest tests/e2e/ -v

# Cobertura
pytest --cov=agents --cov=retriever --cov=document_processor tests/
```

**Conceptos que debo dominar:**
- Cuándo usar mocks vs testing real
- Diferencia entre test de integración y test E2E
- Cómo testear un pipeline de IA que depende de un LLM externo
- Qué métricas de testing son realmente útiles

---

### Bloque 4: Deploy a AWS

**Objetivo:** Desplegar DocChat en un servidor AWS accesible desde internet con HTTPS.

**Conceptos clave:**
- AWS EC2: instancias, security groups, key pairs
- CloudFormation: Infrastructure as Code (IaC)
- User Data: scripts de inicialización al crear una instancia
- Caddy: proxy reverso con HTTPS automático
- DNS: configuración de dominio (opcional)
- Costs: free tier y estimación de costos

**Aplicación a DocChat:**
- Security group: puertos 22 (SSH), 80 (HTTP), 443 (HTTPS), 5000 (Gradio)
- User data: instalar Docker, clonar repo, ejecutar `docker compose up`
- Caddy: terminar HTTPS y redirigir a la app
- Persistencia: volume EBS para datos de ChromaDB

**Arquitectura:**
```
Internet → Caddy (HTTPS) → App (Gradio:5000) → ChromaDB
                                        ↓
                                   Volume EBS (persistencia)
```

**Resultado esperado:**
```bash
# Deploy con CloudFormation
aws cloudformation create-stack \
  --stack-name docchat \
  --template-body file://deploy/cloudformation.yaml

# App accesible en https://tu-dominio.com
```

**Conceptos que debo dominar:**
- Cuándo usar EC2 vs ECS vs Lambda
- Qué es Infrastructure as Code y por qué usarlo
- Cómo manejar secrets (API keys) en producción
- Cómo estimar costos de AWS

---

### Bloque 5: CI/CD con GitHub Actions

**Objetivo:** Automatizar testing y deployment cada vez que se hace push a `main`.

**Conceptos clave:**
- Continuous Integration (CI): ejecutar tests automáticamente
- Continuous Deployment (CD): desplegar automáticamente si los tests pasan
- GitHub Actions: triggers, jobs, steps, secrets
- OIDC: autenticación segura entre GitHub y AWS (sin secrets estáticos)
- Environments: protección de branches, approval gates
- Cache: acelerar builds reutilizando dependencias

**Aplicación a DocChat:**
- **Trigger:** push a `main` o pull request
- **Stage 1 (parallel):** unit tests + linting
- **Stage 2:** build Docker image
- **Stage 3:** integration tests contra Docker Compose
- **Stage 4:** deploy a AWS (solo en `main`, no en PRs)
- **Stage 5:** health check post-deploy

**Estructura del workflow:**
```yaml
name: CI/CD
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - Unit tests
      - Integration tests
  
  build:
    needs: test
    steps:
      - Build Docker image
      - Push a GHCR
  
  deploy:
    needs: build
    if: github.ref == 'refs/heads/main'
    steps:
      - Deploy a EC2 via CloudFormation
      - Health check
```

**Resultado esperado:**
```bash
# Push a main → tests pasan → build → deploy automático
# Pull request → tests pasan → no deploy
# Health check verifica que la app está funcionando
```

**Conceptos que debo dominar:**
- Diferencia entre CI y CD
- Qué es un workflow en GitHub Actions
- Cómo manejar secrets en CI/CD
- Qué es OIDC y por qué es mejor que secrets estáticos
- Cómo implementar rollback si el deploy falla

---

## Decisiones Técnicas

| Decisión | Opciones | Mi elección | Razón |
|----------|----------|-------------|-------|
| Vector store | ChromaDB vs PostgreSQL+pgvector | **ChromaDB** | Simplifica la infraestructura |
| Test framework | pytest vs unittest | **pytest** | Estándar en Python, plugins útiles |
| Cloud provider | AWS vs GCP vs Azure | **AWS** | Más documentación, free tier |
| Container registry | Docker Hub vs GHCR vs ECR | **GHCR** | Gratis con GitHub Actions |
| IaC tool | CloudFormation vs Terraform | **CloudFormation** | Nativo AWS, sin dependencias |
| HTTPS | Caddy vs Nginx + Let's Encrypt | **Caddy** | Automático, más simple |

---

## Orden de Implementación

```
Bloque 1: Docker (1-2 días)
    └→ Crear Dockerfile, docker build, docker run

Bloque 2: Docker Compose (1 día)
    └→ docker-compose.yaml con app + chroma

Bloque 3: Tests con pytest (2-3 días)
    └→ Unit + integration + E2E

Bloque 4: AWS (2-3 días)
    └→ EC2 + CloudFormation + Caddy

Bloque 5: CI/CD (1-2 días)
    └→ GitHub Actions workflow completo
```

**Tiempo total estimado:** 7-11 días de aprendizaje + implementación

---

## Riesgos y Mitigaciones

| Riesgo | Impacto | Mitigación |
|--------|---------|------------|
| ChromaDB no escala en producción | Alto | Usar Chroma Cloud o migrar a pgvector después |
| LLM API costs en tests | Medio | Mockear LLMs en tests unitarios |
| AWS free tier expira | Bajo | Monitorear costs, set up billing alerts |
| Secrets expuestos en repo | Alto | Usar GitHub Secrets, nunca hardcodear |
| Build times lentos | Medio | Cache de Docker layers, dependencias |

---

## Próximos Pasos

Una vez que esta guía esté lista:

1. Crear guía de estudio individual para **Bloque 1: Docker**
2. Implementar Dockerfile para DocChat
3. Crear guía de estudio individual para **Bloque 2: Docker Compose**
4. Implementar docker-compose.yaml
5. Continuar con los bloques restantes

---

## Referencias

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [pytest Documentation](https://docs.pytest.org/)
- [Playwright Python](https://playwright.dev/python/)
- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [AWS CloudFormation](https://docs.aws.amazon.com/cloudformation/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Caddy Documentation](https://caddyserver.com/docs/)

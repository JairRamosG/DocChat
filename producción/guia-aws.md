# Guía AWS - Despliegue de DocChat en la Nube

## Tu proyecto

```
DocChat (Multi-agente RAG):
├── Gradio App (Python web UI)     → Puerto 5000
├── ChromaDB (Vector Database)     → Puerto 8000
├── Document Processing (Docling)  → Interno
└── LLM API Calls (OpenRouter)     → Externo (HTTP)
```

**Servicios que necesitás:**
1. Almacenar la imagen Docker
2. Ejecutar los containers
3. Acceso desde internet
4. Almacenamiento persistente para ChromaDB
5. Variables de entorno seguras (API keys)

---

## ¿Por qué NO Lambda?

```
Lambda:
  ✅ Gratis hasta 1M requests/mes
  ❌ Máximo 15 minutos de ejecución
  ❌ No mantiene estado entre invocaciones
  ❌ ChromaDB necesita almacenamiento persistente
  ❌ Gradio necesita conexión WebSocket persistente
  ❌ Cold start de 2-5 segundos

Fargate:
  ✅ Ejecuta Docker containers
  ✅ Sin límite de tiempo
  ✅ Estado persistente
  ✅ Sin cold start
  ✅ Pay-per-second (solo pagás lo que usás)
```

**Lambda sirve para:** APIs REST simples, procesamiento de archivos, webhooks.
**Tu proyecto necesita:** un servidor corriendo permanentemente con estado.

---

## Arquitectura recomendada para portafolio

```
                    INTERNET
                       │
                       ▼
              ┌────────────────┐
              │   Route 53     │  ← Dominio (opcional)
              │   (DNS)        │
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │      ALB       │  ← Application Load Balancer
              │  (Puerto 80)   │     Distribuye tráfico
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │   ECS Fargate  │  ← Ejecuta tu container
              │  (Gradio App)  │     Sin managing EC2
              │  Puerto 5000   │
              └───────┬────────┘
                      │
          ┌───────────┼───────────┐
          │           │           │
          ▼           ▼           ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ ChromaDB │ │   EFS    │ │ Secrets  │
   │ Fargate  │ │(Almacen.)│ │ Manager  │
   └──────────┘ └──────────┘ └──────────┘
```

---

## Los servicios explicados uno por uno

### 1. ECR (Elastic Container Registry)

**Qué es:** Un repositorio para tus imágenes Docker en AWS.

**Analogía:** Es como GitHub pero para containers en vez de código.

```
Tu máquina:        docker build -t docchat:v1.0 .
ECR:               aws ecr push docchat:v1.0
ECS:               "Dame la imagen docchat:v1.0" → la ejecuta
```

**Para qué lo necesitás:** Para que ECS pueda descargar tu imagen y ejecutarla.

**Costo:** Gratis (almacenamiento de imágenes Docker).

---

### 2. ECS (Elastic Container Service)

**Qué es:** Un servicio que ejecuta y gestiona containers.

**Analogía:** Es como `docker compose up` pero en la nube, con auto-reinicio, escalado, y monitoreo.

```
docker compose up:          ECS Fargate:
- Corre en tu máquina       - Corre en servidores de AWS
- Se muere si apagas        - Se auto-reinicia
- No escala                 - Escala automáticamente
- Sin monitoreo             - CloudWatch integration
```

**Modos de ECS:**
| Modo | Qué es | Para tu portafolio |
|------|--------|-------------------|
| **EC2** | Vos manejás las máquinas virtuales | No recomendado |
| **Fargate** | AWS maneja las máquinas | **Recomendado** |

**Fargate es serverless para containers:** No elegís instancia, no actualizás SO, no manejás nada. Solo decís "corré este container con X CPU y Y RAM".

**Costo:** ~$0.04/hora para 0.5 vCPU + 1GB RAM = ~$29/mes corriendo 24/7.
**Truco:** Si lo apagás cuando no lo usás, pagás solo cuando está encendido.

---

### 3. ALB (Application Load Balancer)

**Qué es:** Recibe tráfico de internet y lo envía a tu container.

**Analogía:** Es como un recepcionista que recibe llamadas y las redirige al empleado correcto.

```
Usuario → www.docchat.com → ALB → ECS Fargate (Gradio)
                                    └─→ ChromaDB
```

**Para qué lo necesitás:**
- Para que tu app sea accesible desde internet
- Para manejar HTTPS (certificado SSL gratis)
- Para distribuir tráfico si escalás

**Costo:** ~$16/mes (siempre corriendo) + $0.008 por horausage.
**Truco:** Para portafolio, podés usar solo la IP pública de ECS sin ALB (más barato).

---

### 4. EFS (Elastic File System)

**Qué es:** Un disco compartido que mantiene datos entre reinicios de containers.

**Analogía:** Es como un USB drive en la nube que todos los containers pueden leer.

```
Sin EFS:
  Container muere → ChromaDB pierde todos los vectores

Con EFS:
  Container muere → Se reinicia → ChromaDB sigue teniendo los vectores
```

**Para qué lo necesitás:** Para que ChromaDB no pierda los embeddings cuando el container se reinicia.

**Costo:** ~$0.30/GB/mes. Si tenés 1GB de embeddings = $0.30/mes.

---

### 5. Secrets Manager

**Qué es:** Un lugar seguro para guardar API keys y contraseñas.

**Analogía:** Es como un cajón fuerte donde guardás las llaves.

```
MAL:   OPENROUTER_API_KEY=sk-xxxxx  (en código o .env)
BIEN:  OPENROUTER_API_KEY → Secrets Manager → ECS lo lee
```

**Para qué lo necesitás:** Para no exponer tu API key de OpenRouter en el código.

**Costo:** ~$0.40/secreto/mes. Con 1-2 secrets = ~$0.80/mes.

---

### 6. CloudWatch

**Qué es:** Sistema de monitoreo y logs de AWS.

**Analogía:** Es como el `docker logs` pero en la nube, con historial y alertas.

```
docker compose logs -f    →    CloudWatch Logs
                                - Historial indefinido
                                - Búsqueda por texto
                                - Métricas automáticas
```

**Costo:** Gratis para logs básicos (5GB/mes).

---

### 7. Route 53 (Opcional)

**Qué es:** Servicio DNS de AWS para dominios personalizados.

```
Sin Route 53:  http://3.15.20.100:5000  (IP fea)
Con Route 53:  https://docchat.tudominio.com  (bonito)
```

**Costo:** $0.50/mes por dominio + $0.40/mes por hosted zone.
**Nota:** Para portafolio, la IP pública es suficiente.

---

## Estrategia de costos para portafolio

### Opción A: Más barato (~$10-15/mes)

```
ECS Fargate (0.25 vCPU, 0.5GB RAM):  ~$15/mes
  + Apagar cuando no lo usás:        ~$5-10/mes
EFS (1GB):                           ~$0.30/mes
Secrets Manager (1 secret):          ~$0.40/mes
CloudWatch Logs:                     Gratis
                                      ─────────
Total:                               ~$6-16/mes
```

### Opción B: Siempre encendido (~$35-45/mes)

```
ECS Fargate (0.5 vCPU, 1GB RAM):    ~$29/mes
ALB:                                 ~$16/mes
EFS (1GB):                           ~$0.30/mes
Secrets Manager (1 secret):          ~$0.40/mes
CloudWatch Logs:                     Gratis
                                      ─────────
Total:                               ~$46/mes
```

### Opción C: EC2 (más barato para 24/7)

```
EC2 t3.micro (1 vCPU, 1GB RAM):     ~$8/mes (us-east-1)
EBS (20GB):                          ~$2/mes
EIP (IP estática):                   Gratis
Security Group:                      Gratis
                                      ─────────
Total:                               ~$10/mes
```

**Recomendación para portafolio:** Opción A (Fargate apagable) o Opción C (EC2 siempre encendido).

---

## Cómo interactúan los servicios

### Flujo de despliegue

```
1. Vos: docker build -t docchat:v1.0 .
2. Vos: aws ecr create-repository --repository-name docchat
3. Vos: docker tag docchat:v1.0 <ecr-url>:v1.0
4. Vos: docker push <ecr-url>:v1.0
5. AWS: "Guardé tu imagen en ECR"
6. Vos: aws ecs create-service --task-definition docchat
7. AWS: "Descargo la imagen de ECR, creo el container, lo conecto a ALB"
8. Usuario: www.docchat.com → ALB → ECS → Tu app
```

### Flujo de ejecución

```
Usuario sube documento
    → ALB recibe request
    → ECS (Gradio) recibe el archivo
    → Docling procesa el documento
    → Embeddings se guardan en ChromaDB (con EFS)
    → Usuario hace pregunta
    → Relevance Checker verifica
    → Research Agent genera respuesta
    → Verification Agent verifica
    → Respuesta vuelve al usuario
```

---

## Guía paso a paso: Despliegue con ECS Fargate

### Paso 1: Crear repositorio ECR

```bash
# Instalar AWS CLI (si no lo tenés)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configurar credenciales
aws configure
# Access Key ID: <tu-access-key>
# Secret Access Key: <tu-secret-key>
# Region: us-east-1
# Output: json

# Crear repositorio ECR
aws ecr create-repository --repository-name docchat --region us-east-1
```

### Paso 2: Subir imagen Docker a ECR

```bash
# Login a ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Taggear la imagen
docker build -t docchat:v1.0 .
docker tag docchat:v1.0 <account-id>.dkr.ecr.us-east-1.amazonaws.com/docchat:v1.0

# Push a ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/docchat:v1.0
```

### Paso 3: Crear ECS Cluster

```bash
# Crear cluster Fargate
aws ecs create-cluster --cluster-name docchat-cluster --capacity-providers FARGATE
```

### Paso 4: Crear Task Definition

```json
// docchat-task.json
{
  "family": "docchat-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "docchat-app",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/docchat:v1.0",
      "portMappings": [
        {
          "containerPort": 5000,
          "hostPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "CHROMA_HOST",
          "value": "localhost"
        },
        {
          "name": "CHROMA_PORT",
          "value": "8000"
        }
      ],
      "secrets": [
        {
          "name": "OPENROUTER_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:docchat/openrouter-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/docchat",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    },
    {
      "name": "chroma",
      "image": "chromadb/chroma:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "hostPort": 8000,
          "protocol": "tcp"
        }
      ],
      "mountPoints": [
        {
          "sourceVolume": "chroma-data",
          "containerPath": "/chroma/chroma"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/docchat",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ],
  "volumes": [
    {
      "name": "chroma-data",
      "efsVolumeConfiguration": {
        "fileSystemId": "<efs-id>",
        "rootDirectory": "/"
      }
    }
  ]
}
```

```bash
# Registrar task definition
aws ecs register-task-definition --cli-input-json file://docchat-task.json
```

### Paso 5: Crear Service

```bash
# Crear service
aws ecs create-service \
  --cluster docchat-cluster \
  --service-name docchat-service \
  --task-definition docchat-task \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<subnet-id>],securityGroups=[<sg-id>],assignPublicIp=ENABLED}"
```

### Paso 6: Verificar

```bash
# Ver estado del service
aws ecs describe-services --cluster docchat-cluster --services docchat-service

# Ver logs
aws logs tail /ecs/docchat --follow
```

---

## Checklist de seguridad

```
□ API key de OpenRouter en Secrets Manager (NO en código)
□ Security Group solo abre puertos 80 y 443
□ IAM Role con permisos mínimos (Least Privilege)
□ EFS con encryption at rest
□ Logs habilitados en CloudWatch
□ No hardcodear credenciales en Dockerfile
```

---

## Errores comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `CannotPullContainerError` | ECR no accesible | Verificar IAM Role del ECS |
| `Essential container exited` | App crashea al iniciar | Ver logs en CloudWatch |
| `Timeout waiting for network` | Security Group bloquea | Abrir puertos en SG |
| `EFS mount failed` | FileSystemId incorrecto | Verificar EFS ID |

---

## Siguiente paso

Una vez que entiendas esto, pasamos a:
1. **Crear cuenta AWS** (si no la tenés)
2. **Configurar AWS CLI** en tu máquina
3. **Crear los recursos** paso a paso
4. **Desplegar y probar**

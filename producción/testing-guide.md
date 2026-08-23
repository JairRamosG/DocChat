# Testing con pytest - Guia Practica

## Por que existen los tests?

**El problema que resuelven:**

```
Tu app funciona bien
Haces un cambio
"Ahora no funciona"
No sabes que rompiste
Tienes que buscar el error manualmente
```

**Los tests resuelven esto:** Ejecutan tu codigo automaticamente y te avisan si algo se rompio.

## Analogia simple

Piensa en tests como un **control de calidad**:

```
Sin tests:
  - Cocinas un platillo
  - Lo sirves
  - Si esta malo, el cliente se enferma

Con tests:
  - Cocinas el platillo
  - Pruebas antes de servir
  - Si esta malo, lo arreglas antes
  - El cliente nunca se entera
```

## Los 3 tipos de tests

| Tipo | Que prueba | Rapidez | Cuanto cuesta |
|------|------------|---------|---------------|
| **Unit** | Funciones individuales | Muy rapido | Barato |
| **Integration** | Varios componentes juntos | Rapido | Medio |
| **E2E** | Todo el flujo completo | Lento | Caro |

### Unit Tests

Prueban **una funcion aislada**:

```python
# Sin dependencias externas
def test_sumar():
    assert sumar(2, 3) == 5

def test_dividir():
    assert dividir(10, 2) == 5
```

**Ventajas:**
- Rapidos (milisegundos)
- Faciles de escribir
- Faciles de arreglar

### Integration Tests

Prueban **varios componentes juntos**:

```python
# Prueba que la app se conecta a ChromaDB
def test_chromadb_connection():
    client = ChromaClient()
    client.add_documents(docs)
    results = client.search("query")
    assert len(results) > 0
```

**Ventajas:**
- Prueban que todo funciona junto
- Descubren problemas de integracion

### E2E Tests (End-to-End)

Prueban **el flujo completo del usuario**:

```python
# Simula un usuario usando la app
def test_full_flow():
    # 1. Subir documento
    upload_document("test.pdf")
    
    # 2. Hacer pregunta
    answer = ask_question("Que dice el documento?")
    
    # 3. Verificar respuesta
    assert "respuesta" in answer.lower()
```

**Ventajas:**
- Prueban la experiencia real del usuario
- Descubren problemas de usabilidad

## La piramide de testing

```
        /\
       /  \        E2E (pocos, lentos, caros)
      /    \
     /------\      Integration (algunos, rapidos)
    /        \
   /----------\    Unit (muchos, muy rapidos, baratos)
```

**Regla:** Mas unit tests, menos E2E tests.

## Por que pytest?

| Herramienta | Ventaja |
|-------------|---------|
| **pytest** | Simple, rapido, mucho ecosistema |
| unittest | Oficial de Python, mas verboso |
| nose2 | Similar a pytest, menos popular |

**pytest es el estandar en la industria Python.**

## Estructura basica

```
DocChat/
├── app.py
├── agents/
├── retriever/
├── tests/                    # ← Carpeta de tests
│   ├── unit/
│   │   ├── test_retriever.py
│   │   └── test_agents.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── conftest.py          # ← Fixtures compartidos
└── pytest.ini               # ← Configuracion
```

## Creando tu primer test

### Paso 1: Crear archivo de test

```python
# tests/unit/test_retriever.py

def test_sumar():
    """Test basico de una funcion."""
    resultado = 2 + 3
    assert resultado == 5
```

### Paso 2: Ejecutar el test

```bash
pytest
```

Resultado:
```
tests/unit/test_retriever.py .    [100%]
============================== 1 passed ==============================
```

### Paso 3: Ver que pasa con un error

```python
def test_dividir():
    """Test que falla."""
    resultado = 10 / 0  # Error: division por cero
    assert resultado == 5
```

```bash
pytest
```

Resultado:
```
FAILED tests/unit/test_retriever.py::test_dividir - ZeroDivisionError
============================== 1 failed ==============================
```

## La palabra clave assert

`assert` es la base de todos los tests:

```python
# Verificar igualdad
assert resultado == esperado

# Verificar que algo es True
assert es_valido is True

# Verificar que algo no esta vacio
assert len(lista) > 0

# Verificar que lanza un error
with pytest.raises(ValueError):
    funcion_que_falla()
```

## Organizando tests

### Unit tests

```python
# tests/unit/test_document_processor.py

import pytest
from document_processor.file_handler import DocumentProcessor

class TestDocumentProcessor:
    """Tests para DocumentProcessor."""
    
    def setup_method(self):
        """Configurar antes de cada test."""
        self.processor = DocumentProcessor()
    
    def test_validate_files_valid(self):
        """Test que archivos validos pasan la validacion."""
        files = ["doc1.pdf", "doc2.txt"]
        # No debe lanzar error
        self.processor.validate_files(files)
    
    def test_validate_files_invalid(self):
        """Test que archivos invalidos fallan."""
        files = ["doc.exe"]  # Formato no permitido
        with pytest.raises(ValueError):
            self.processor.validate_files(files)
```

### Integration tests

```python
# tests/integration/test_pipeline.py

import pytest
from retriever.builder import RetrieverBuilder

@pytest.mark.integration
class TestRetriever:
    """Tests que requieren ChromaDB."""
    
    def test_build_retriever(self):
        """Test que el retriever se construye correctamente."""
        builder = RetrieverBuilder()
        docs = ["documento de prueba"]
        retriever = builder.build_hybrid_retriever(docs)
        assert retriever is not None
```

## Markers: etiquetando tests

Los markers te permiten **filtrar tests**:

```python
import pytest

@pytest.mark.unit
def test_rapido():
    """Test unitario."""
    pass

@pytest.mark.integration
def test_lento():
    """Test de integracion."""
    pass

@pytest.mark.slow
def test_muy_lento():
    """Test E2E."""
    pass
```

### Ejecutar por marker

```bash
# Solo unit tests
pytest -m unit

# Solo integration
pytest -m integration

# Todos excepto slow
pytest -m "not slow"
```

## Fixtures: datos reutilizables

Los fixtures son **datos de prueba compartidos**:

```python
# tests/conftest.py

import pytest

@pytest.fixture
def sample_document():
    """Fixture: documento de prueba."""
    return {
        "content": "Este es un documento de prueba",
        "metadata": {"source": "test"}
    }

@pytest.fixture
def sample_documents():
    """Fixture: varios documentos."""
    return [
        {"content": "Documento 1", "metadata": {}},
        {"content": "Documento 2", "metadata": {}},
    ]
```

### Usando fixtures

```python
# tests/unit/test_document.py

def test_process_document(sample_document):
    """Test que usa el fixture."""
    processor = DocumentProcessor()
    result = processor.process(sample_document["content"])
    assert result is not None
```

## Mocking: simulando dependencias

Los mocks te permiten **simular servicios externos**:

```python
from unittest.mock import Mock, patch

def test_llamar_api():
    """Test que simula una llamada a API."""
    
    # Crear mock
    mock_api = Mock()
    mock_api.return_value = {"respuesta": "test"}
    
    # Usar mock
    with patch('requests.get', mock_api):
        resultado = llamar_api("https://api.ejemplo.com")
    
    # Verificar
    assert resultado["respuesta"] == "test"
    mock_api.assert_called_once()
```

**Por que usar mocks?**
- No dependes de servicios externos
- Tests mas rapidos
- Tests mas predecibles

## Ejecutando tests

### Comandos basicos

```bash
# Ejecutar todos los tests
pytest

# Ejecutar un archivo especifico
pytest tests/unit/test_retriever.py

# Ejecutar un test especifico
pytest tests/unit/test_retriever.py::test_sumar

# Ver detalles
pytest -v

# Ver prints (si los tienes)
pytest -s

# Parar en el primer error
pytest -x
```

### Con cobertura

```bash
# Instalar plugin
pip install pytest-cov

# Ejecutar con cobertura
pytest --cov=agents --cov=retriever

# Reporte HTML
pytest --cov=agents --cov-report=html
```

### Output

```
Name                          Stmts   Miss  Cover
-------------------------------------------------
agents/relevance_checker.py      45     12    73%
agents/research_agent.py         62     18    71%
retriever/builder.py             38      8    79%
-------------------------------------------------
TOTAL                           145     38    74%
```

## Buenas practicas

### 1. Nombra los tests descriptivamente

```python
# MAL
def test_funcion():
    pass

# BIEN
def test_retriever_returns_results_for_valid_query():
    pass
```

### 2. Un assert por test (idealmente)

```python
# MAL
def test_retriever():
    assert retriever is not None
    assert len(results) > 0
    assert results[0] == expected

# BIEN
def test_retriever_is_not_none():
    assert retriever is not None

def test_retriever_returns_results():
    assert len(results) > 0
```

### 3. Tests independientes

```python
# MAL: depende de otro test
def test_crear_documento():
    global doc
    doc = crear_documento()

def test_usar_documento():
    usar(doc)  # Falla si test_crear_documento no corre primero

# BIEN: cada test es independiente
def test_crear_documento():
    doc = crear_documento()
    assert doc is not None
```

### 4. Datos de prueba claros

```python
# MAL
assert func(1) == 2

# BIEN
def test_sumar_dos_numeros():
    assert sumar(2, 3) == 5
```

### 5. Tests rapidos

```python
# MAL: test que tarda 30 segundos
def test_api_real():
    response = requests.get("https://api.lenta.com")
    assert response.status_code == 200

# BIEN: mock rapido
def test_api_mock():
    with patch('requests.get') as mock:
        mock.return_value.status_code = 200
        response = requests.get("https://api.lenta.com")
    assert response.status_code == 200
```

## En que etapa se hacen los tests?

### TDD (Test-Driven Development)

```
1. Escribir test (que falla)
2. Escribir codigo minimo (que pase el test)
3. Refactorizar
4. Repetir
```

### Desarrollo normal

```
1. Escribir codigo
2. Escribir tests
3. Verificar que pasan
4. Refactorizar
```

### Pre-commit

```bash
# Antes de hacer commit
pytest

# Si pasa, hacer commit
git add .
git commit -m "feat: nueva funcionalidad"
```

## Que se hace con los tests en el dia a dia?

### 1. Desarrollo

```bash
# Mientras programo
pytest tests/unit/ -v

# Verifico que no rompi nada
pytest -x
```

### 2. Pre-commit

```bash
# Antes de commitear
pytest

# Si pasa, commiteo
git commit -m "feat: agregar funcion X"
```

### 3. CI/CD

```yaml
# GitHub Actions
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest
```

### 4. Code Review

```bash
# Cuando alguien hace PR
pytest --cov=agents
# Revisar cobertura minima aceptable
```

## Cobertura de codigo

La cobertura indica **que porcentaje de tu codigo esta testado**:

| Cobertura | Que significa |
|-----------|---------------|
| 0% | Nada testado |
| 50% | La mitad testada |
| 80% | Buena cobertura |
| 100% | Todo testado (raro) |

**Recomendacion:** 70-80% es suficiente para la mayoria de proyectos.

### Ver cobertura

```bash
pytest --cov=agents --cov-report=term-missing
```

```
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
agents/workflow.py               85     15    82%   45-50, 67-72
agents/research_agent.py         62     18    71%   23-28, 45-50
-----------------------------------------------------------
TOTAL                           147     33    78%
```

## Errores comunes

### 1. Test que falla intermitentemente

```python
# MAL: depende del tiempo
def test_api():
    time.sleep(10)  # Esperar 10 segundos
    response = requests.get(url)

# BIEN: retry con timeout
def test_api():
    response = requests.get(url, timeout=5)
    assert response.status_code == 200
```

### 2. Test que depende de estado

```python
# MAL: depende de que se ejecute primero
def test_crear_usuario():
    usuario = crear_usuario("test")

def test_buscar_usuario():
    # Falla si test_crear_usuario no corre
    usuario = buscar_usuario("test")

# BIEN: cada test crea su estado
def test_buscar_usuario_creado():
    crear_usuario("test")
    usuario = buscar_usuario("test")
    assert usuario is not None
```

### 3. Test muy lento

```python
# MAL: test E2E en unit tests
def test_flujo_completo():
    for i in range(1000):
        procesar_documento(i)

# BIEN: test rapido
def test_procesar_documento():
    resultado = procesar_documento("doc.pdf")
    assert resultado is not None
```

## Resumen

| Concepto | Que es | Ejemplo |
|----------|--------|---------|
| **Test** | Verificar que algo funciona | `assert resultado == esperado` |
| **Unit** | Probar una funcion | `test_sumar()` |
| **Integration** | Probar varios componentes | `test_chromadb()` |
| **E2E** | Probar todo el flujo | `test_subir_pregunta()` |
| **Fixture** | Datos de prueba reutilizables | `@pytest.fixture` |
| **Mock** | Simular dependencias | `@patch('requests.get')` |
| **Marker** | Etiquetar tests | `@pytest.mark.unit` |
| **Coverage** | Porcentaje de codigo testado | `--cov=agents` |

## Flujo completo

```
1. Escribir codigo
2. Escribir tests unitarios
3. Escribir tests de integracion
4. Ejecutar: pytest
5. Verificar cobertura: pytest --cov
6. Hacer commit
7. CI ejecuta tests automaticamente
```

## Siguiente paso

Una vez que entiendas esto, pasamos a:
- **CI/CD**: Automatizar tests cada vez que haces push
- **AWS**: Desplegar en la nube

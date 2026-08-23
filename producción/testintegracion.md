# Pruebas de Integración - Guía para Principiantes

## ¿Para qué existen las pruebas de integración?

**Imagina esto:**

```
Tus pruebas unitarias pasan PERFECTAMENTE
Pero cuando juntas los módulos, todo falla
El retriever no le pasa bien los datos al agente
El agente no entiende el formato del verificador
No sabes dónde está el problema
```

**Con pruebas de integración:**

```
Tus pruebas unitarias pasan
Tus pruebas de integración también pasan
SABES que los módulos trabajan juntos correctamente
Si algo falla, SABES qué módulo se rompió
```

## ¿Qué es una prueba de integración?

Es **verificar que VARIOS MÓDULOS trabajen juntos correctamente**.

```python
# Prueba unitaria: testea UNA función
def test_retriever_search():
    retriever = MockRetriever()
    result = retriever.search("query")
    assert result is not None

# Prueba de integración: testea VARIOS módulos juntos
def test_retriever_to_agent():
    # DADO: un retriever real con documentos
    docs = [Document(page_content="Python es un lenguaje")]
    retriever = build_retriever(docs)
    
    # CUANDO: el agente usa el retriever
    agent = ResearchAgent()
    result = agent.generate("¿Qué es Python?", retriever.invoke("Python"))
    
    # ENTONCES: el resultado debe ser coherente
    assert "lenguaje" in result["draft_answer"].lower()
```

## Unit vs Integración: ¿Cuál uso cuándo?

| Tipo | Qué testea | Velocidad | Créditos API | Cuándo usar |
|------|-----------|-----------|--------------|-------------|
| **Unitaria** | 1 función aislada | ⚡ Rápido | ❌ NO | Siempre |
| **Integración** | Módulos trabajando juntos | 🐢 Medio | ⚡ SÍ* | Después de unit |
| **E2E** | Flujo completo de usuario | 🐌 Lento | ⚡ SÍ | Antes de deploy |

*Depende de si mockes las APIs externas

## La regla de oro

> **Las pruebas unitarias verifican QUE funciona.  
> Las pruebas de integración verifican CÓMO funciona junto.**

## Estructura de carpetas

```
tests/
├── unit/                    # Pruebas unitarias (ya tienes)
│   ├── test_constants.py
│   ├── test_settings.py
│   └── ...
├── integration/             # Pruebas de integración (NUEVO)
│   ├── __init__.py
│   ├── test_retriever_agent.py
│   ├── test_document_pipeline.py
│   ├── test_workflow_integration.py
│   └── conftest.py          # Fixtures compartidos
└── pipeline/                # Pruebas E2E (futuro)
    ├── __init__.py
    └── test_full_pipeline.py
```

## Conftest: Los fixtures compartidos

**`conftest.py`** es donde guardas fixtures que usan VARIOS tests de integración.

```python
# tests/integration/conftest.py
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document


@pytest.fixture
def sample_documents():
    """Documentos de prueba para integración."""
    return [
        Document(
            page_content="Python es un lenguaje de programación interpretado.",
            metadata={"source": "test.pdf"}
        ),
        Document(
            page_content="Python fue creado por Guido van Rossum en 1991.",
            metadata={"source": "test.pdf"}
        ),
        Document(
            page_content="Python se usa para inteligencia artificial y ciencia de datos.",
            metadata={"source": "test.pdf"}
        ),
    ]


@pytest.fixture
def mock_retriever():
    """Retriever mock que retorna documentos de prueba."""
    retriever = MagicMock()
    retriever.invoke.return_value = [
        Document(page_content="Python es un lenguaje de programación.")
    ]
    return retriever


@pytest.fixture
def mock_openrouter():
    """Mock de OpenRouter API para no gastar créditos."""
    with patch("langchain_openrouter.ChatOpenRouter.invoke") as mock:
        mock.return_value = MagicMock(
            content="Python es un lenguaje interpretado creado en 1991."
        )
        yield mock
```

## Los 5 tipos de pruebas de integración

### 1. Prueba de flujo de datos

**¿Los datos fluyen correctamente entre módulos?**

```python
def test_retriever_passes_docs_to_agent(sample_documents):
    """Verifica que el retriever pasa documentos al agente."""
    # GIVEN
    retriever = MagicMock()
    retriever.invoke.return_value = sample_documents
    
    agent = ResearchAgent()
    agent.model = MagicMock()
    agent.model.invoke.return_value = MagicMock(content="Respuesta")
    
    # WHEN
    docs = retriever.invoke("¿Qué es Python?")
    result = agent.generate("¿Qué es Python?", docs)
    
    # THEN
    assert len(docs) == 3
    assert "draft_answer" in result
```

### 2. Prueba de formato

**¿El output de un módulo es compatible con el input del siguiente?**

```python
def test_agent_output_format_for_verifier():
    """Verifica que el output del agente es válido para el verificador."""
    # GIVEN
    agent = ResearchAgent()
    agent.model = MagicMock()
    agent.model.invoke.return_value = MagicMock(content="Python es un lenguaje.")
    
    verifier = VerificationAgent()
    verifier.structured_model = MagicMock()
    verifier.structured_model.invoke.return_value = VerificationReport(
        supported="YES", relevant="YES"
    )
    
    # WHEN
    mock_doc = Document(page_content="Python es un lenguaje.")
    agent_result = agent.generate("¿Qué es Python?", [mock_doc])
    
    # Verificar que el output del agente funciona como input del verificador
    verifier_result = verifier.check(agent_result["draft_answer"], [mock_doc])
    
    # THEN
    assert "verification_report" in verifier_result
```

### 3. Prueba de comportamiento conjunto

**¿Los módulos toman decisiones correctas juntos?**

```python
def test_relevance_checker_to_research_flow():
    """Verifica el flujo: relevancia → investigación."""
    # GIVEN
    checker = RelevanceChecker()
    checker.model = MagicMock()
    checker.model.invoke.return_value = MagicMock(content="CAN_ANSWER")
    
    researcher = ResearchAgent()
    researcher.model = MagicMock()
    researcher.model.invoke.return_value = MagicMock(content="Respuesta")
    
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = [
        Document(page_content="Contenido relevante")
    ]
    
    # WHEN
    classification = checker.check("¿Qué es Python?", mock_retriever)
    
    if classification == RelevanceClassification.CAN_ANSWER:
        docs = mock_retriever.invoke("¿Qué es Python?")
        result = researcher.generate("¿Qué es Python?", docs)
    
    # THEN
    assert classification == RelevanceClassification.CAN_ANSWER
    assert "draft_answer" in result
```

### 4. Prueba de manejo de errores

**¿Qué pasa cuando un módulo falla?**

```python
def test_workflow_handles_api_error():
    """Verifica que el workflow maneja errores de API."""
    # GIVEN
    with patch("agents.workflow.ResearchAgent") as MockAgent:
        MockAgent.return_value.generate.side_effect = Exception("API Error")
        
        workflow = AgentWorkflow()
        workflow.researcher = MockAgent.return_value
        
        # WHEN/THEN
        with pytest.raises(Exception):
            workflow._research_step({
                "question": "test",
                "documents": [Document(page_content="test")]
            })
```

### 5. Prueba de rendimiento básico

**¿Los módulos trabajan juntos sin ser extremadamente lentos?**

```python
import time

def test_retriever_to_agent_performance(sample_documents):
    """Verifica que el flujo completo toma menos de 5 segundos."""
    # GIVEN
    retriever = MagicMock()
    retriever.invoke.return_value = sample_documents
    
    agent = ResearchAgent()
    agent.model = MagicMock()
    agent.model.invoke.return_value = MagicMock(content="Respuesta")
    
    # WHEN
    start = time.time()
    docs = retriever.invoke("test")
    result = agent.generate("test", docs)
    elapsed = time.time() - start
    
    # THEN
    assert elapsed < 5.0  # Debe tomar menos de 5 segundos
```

## ¿Cuándo MOCKEAR y cuándo NO?

### ✅ SÍ mockear:

```python
# APIs externas (OpenRouter, ChromaDB)
def test_with_mock_api():
    with patch("langchain_openrouter.ChatOpenRouter.invoke") as mock:
        mock.return_value = MagicMock(content="respuesta")
        # ...

# Base de datos
def test_with_mock_db():
    with patch("retriever.builder.Chroma") as mock:
        mock.from_documents.return_value = MagicMock()
        # ...
```

### ❌ NO mockear (en integración):

```python
# Módulos internos que estás probando juntos
def test_real_flow():
    # NO mockees ResearchAgent si estás probando que funciona con VerificationAgent
    agent = ResearchAgent()
    verifier = VerificationAgent()
    
    # Usa mocks SOLO para dependencias externas
    agent.model = MagicMock()
    verifier.structured_model = MagicMock()
```

## Ejemplo real: DocChat

### Flujo completo de integración

```python
# tests/integration/test_docchat_flow.py

def test_full_docchat_flow():
    """Test que verifica el flujo completo: documentos → respuesta."""
    # GIVEN: documentos procesados
    documents = [
        Document(page_content="LangChain es un framework para LLMs."),
        Document(page_content="ChromaDB es una base de datos vectorial."),
    ]
    
    # Mock de APIs externas
    with patch("langchain_openrouter.ChatOpenRouter.invoke") as mock_llm:
        mock_llm.return_value = MagicMock(
            content="LangChain y ChromaDB son herramientas de IA."
        )
        
        # WHEN: ejecutar el flujo
        retriever = MagicMock()
        retriever.invoke.return_value = documents
        
        agent = ResearchAgent()
        agent.model = mock_llm
        
        result = agent.generate("¿Qué son LangChain y ChromaDB?", documents)
        
        # THEN: verificar resultado
        assert "draft_answer" in result
        assert len(result["context_used"]) > 0
```

## Errores comunes de principiantes

### ❌ Error 1: Mockear demasiado

```python
# MAL: mockeas todo, no estás probando nada real
def test_bad_integration():
    with patch("agents.ResearchAgent"):
        with patch("agents.VerificationAgent"):
            with patch("retriever.RetrieverBuilder"):
                # Aquí no estás probando integración real
                pass

# BIEN: mockea solo lo externo
def test_good_integration():
    agent = ResearchAgent()
    verifier = VerificationAgent()
    
    # Solo mockear la API de OpenRouter
    agent.model = MagicMock()
    verifier.structured_model = MagicMock()
```

### ❌ Error 2: Tests muy lentos

```python
# MAL: depende de API real (tarda 10+ segundos)
def test_slow():
    result = real_agent.generate("pregunta", real_docs)  # Llamada real a API
    assert result is not None

# BIEN: mockea la API
def test_fast():
    agent = ResearchAgent()
    agent.model = MagicMock()
    agent.model.invoke.return_value = MagicMock(content="respuesta")
    result = agent.generate("pregunta", fake_docs)
    assert result is not None
```

### ❌ Error 3: Tests que dependen de orden

```python
# MAL: test B depende de que test A corra primero
def test_a_create_user():
    global user_id
    user_id = create_user("test")

def test_b_use_user():
    # Falla si test_a no corrió
    result = get_user(user_id)
    assert result.name == "test"

# BIEN: cada test es independiente
def test_use_user():
    user = create_user("test")  # Crea su propio usuario
    result = get_user(user.id)
    assert result.name == "test"
```

## Checklist antes de escribir integración

```
□ ¿Qué módulos están involucrados?
□ ¿Cómo fluyen los datos entre ellos?
□ ¿Qué dependencias externas necesito mockear?
□ ¿Qué output genera un módulo que es input del siguiente?
□ ¿Qué errores pueden ocurrir en la cadena?
```

## La regla de oro para integración

> **Si la prueba puede explicarse con "DADO esto, CUANDO hago esto, ENTONCES espero esto", está bien escrita.**

```python
# BIEN
def test_retriever_to_agent():
    """DADO un retriever con documentos,
       CUANDO el agente genera una respuesta,
       ENTONCES el resultado contiene la información."""
    # ...

# MAL
def test_integration():
    """Test de integración."""
    # ...
```

## Resumen: estructura de una prueba de integración

```python
def test_nombre_descriptivo():
    """Descripción clara de qué se prueba."""
    # GIVEN (DADO)
    # Preparar el escenario
    
    # WHEN (CUANDO)
    # Ejecutar la acción
    
    # THEN (ENTONCES)
    # Verificar el resultado
```

## Ejercicio práctico

Crea una prueba de integración que:

```
1. Tome documentos de prueba
2. Los pase a ResearchAgent
3. Verifique que el output tiene draft_answer
4. Pase ese output a VerificationAgent
5. Verifique que el verification_report es válido
```

## Siguiente paso

Una vez que entiendas esto, pasamos a:
- **Fixtures avanzados**: `conftest.py` con setup complejo
- **Parametrized tests**: Múltiples casos con una función
- **CI/CD**: Ejecutar tests automáticamente en GitHub

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

---

## Los 8 Pilares de Testing de Integración para Sistemas Multi-Agente

Antes de escribir cualquier test, identificá CUÁL de estos pilares estás atacando. Cada test debe cubrir al menos uno.

### Pilar 1: Flujo de datos entre nodos (Data Flow)

**¿El output de un nodo es exactamente lo que el siguiente nodo espera?**

Cada nodo recibe un output y lo usa como input. Si el formato no coincide, el sistema falla silenciosamente o crashea.

```python
# Ejemplo de problema:
# check_relevance retorna {"is_relevant": True}
# research espera documents en el state
# Si research no recibe documents → error

# Test que verifica esto:
def test_research_receives_documents():
    """Verifica que research recibe los documentos de check_relevance."""
    # GIVEN
    state = {
        "question": "¿Qué es Python?",
        "documents": [Document(page_content="Python es un lenguaje")],
        "is_relevant": True
    }
    
    # WHEN
    workflow = AgentWorkflow()
    result = workflow._research_step(state)
    
    # THEN
    assert "draft_answer" in result
    assert len(result["draft_answer"]) > 0
```

**Qué testear:**
- Que el output de cada nodo sea el tipo de dato correcto
- Que los campos obligatorios estén presentes
- Que no se pierda información entre nodos

---

### Pilar 2: Manejo de estado (State Threading)

**¿El AgentState se mantiene íntegro a lo largo del grafo?**

LangGraph usa un diccionario `AgentState` que se va modificando. Cada nodo escribe algo y el siguiente lo lee.

```python
# Ejemplo de problema:
# check_relevance escribe is_relevant=True
# _decide_after_relevance_check lee is_relevant
# Si el campo no existe → KeyError

# Test que verifica esto:
def test_state_maintains_all_fields():
    """Verifica que el state tiene todos los campos necesarios."""
    required_keys = [
        "question", "documents", "draft_answer",
        "verification_report", "is_relevant", "retriever"
    ]
    
    state = AgentState(
        question="test",
        documents=[],
        draft_answer="",
        verification_report="",
        is_relevant=False,
        retriever=MagicMock()
    )
    
    for key in required_keys:
        assert key in state
```

**Qué testear:**
- Que cada campo del state se mantenga entre nodos
- Que no se sobreescriba información importante
- Que los campos opcionales tengan defaults válidos

---

### Pilar 3: Rutinado condicional (Routing)

**¿Las bifurcaciones del grafo llevan al nodo correcto?**

El grafo tiene decisiones. Si el routing falla, el sistema va por el camino equivocado.

```python
# Ejemplo de problema:
# RelevanceClassifier retorna "CAN_ANSWER"
# Pero el routing lo manda a END en vez de research

# Test que verifica esto:
def test_can_answer_routes_to_research():
    """Verifica que CAN_ANSWER va a research, no a END."""
    # GIVEN
    workflow = AgentWorkflow()
    state = {"is_relevant": True}
    
    # WHEN
    result = workflow._decide_after_relevance_check(state)
    
    # THEN
    assert result == "relevant"  # Debe ir a research

def test_no_match_routes_to_end():
    """Verifica que NO_MATCH va a END."""
    workflow = AgentWorkflow()
    state = {"is_relevant": False}
    result = workflow._decide_after_relevance_check(state)
    assert result == "irrelevant"
```

**Qué testear:**
- Que cada clasificación lleve al nodo correcto
- Que NO_MATCH no llegue a research
- Que verify con Supported: NO haga re_research
- Que Supported: YES termine en END

---

### Pilar 4: Formateo de respuestas del LLM (LLM Output Contract)

**¿El sistema tolera respuestas malformadas del LLM?**

Los LLMs son impredecibles. A veces responden "YES", a veces "Yes", a veces "YES.".

```python
# Ejemplo de problema:
# RelevanceChecker espera: "CAN_ANSWER", "PARTIAL", "NO_MATCH"
# LLM responde: "Yes, can answer" → ValueError → NO_MATCH silencioso

# Test que verifica esto:
def test_handles_malformed_llm_response():
    """Verifica que el sistema maneja respuestas inválidas del LLM."""
    # GIVEN
    checker = RelevanceChecker()
    checker.model = MagicMock()
    
    # LLM responde algo inválido
    mock_response = MagicMock()
    mock_response.content = "Yes, I think this is relevant"
    checker.model.invoke.return_value = mock_response
    
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = [MagicMock()]
    
    # WHEN
    result = checker.check("test question", mock_retriever)
    
    # THEN
    # Debe caer en NO_MATCH, no crashear
    assert result == RelevanceClassification.NO_MATCH
```

**Qué testear:**
- Respuestas con formato inesperado (maiúsculas, espacios, puntuación)
- Respuestas vacías del LLM
- Respuestas en idioma diferente
- Strings muy largos o muy cortos

---

### Pilar 5: Manejo de errores y resiliencia (Error Propagation)

**¿Cuándo algo falla, el sistema lo maneja graciosamente?**

Cuando un componente falla, el sistema debe producir un resultado controlado, no un crash.

```python
# Ejemplo de problema:
# OpenRouter API cae → ResearchAgent lanza excepción
# El workflow no la maneja → la app crashea

# Test que verifica esto:
def test_workflow_handles_api_error():
    """Verifica que el workflow maneja errores de API."""
    # GIVEN
    workflow = AgentWorkflow()
    workflow.researcher = MagicMock()
    workflow.researcher.generate.side_effect = Exception("API Error")
    
    state = {"question": "test", "documents": [MagicMock()]}
    
    # WHEN/THEN
    # No debe crashear el workflow completo
    with pytest.raises(Exception):
        workflow._research_step(state)
```

**Qué testear:**
- API de OpenRouter cae → fallback o mensaje de error
- ChromaDB no responde → retry o degradación
- Documento corrupto → skip, no crash
- Timeout del LLM → respuesta por defecto

---

### Pilar 6: Integridad del contexto (Context Integrity)

**¿El contexto viaja completo desde los documentos hasta la respuesta final?**

El contexto se puede corruptear o perder por el camino.

```python
# Ejemplo de problema:
# research usa 3 documentos para generar respuesta
# verify recibe solo 1 documento → verificación incompleta

# Test que verifica esto:
def test_context_preserved_between_research_and_verify():
    """Verifica que verify recibe el mismo contexto que research."""
    # GIVEN
    documents = [
        Document(page_content="Doc 1: Python es un lenguaje"),
        Document(page_content="Doc 2: Fue creado en 1991"),
        Document(page_content="Doc 3: Se usa para IA"),
    ]
    
    agent = ResearchAgent()
    agent.model = MagicMock()
    agent.model.invoke.return_value = MagicMock(content="Python es un lenguaje de IA")
    
    verifier = VerificationAgent()
    verifier.structured_model = MagicMock()
    verifier.structured_model.invoke.return_value = VerificationReport(
        supported="YES", relevant="YES"
    )
    
    # WHEN
    agent_result = agent.generate("¿Qué es Python?", documents)
    context_used = agent_result["context_used"]
    
    # THEN
    assert "Doc 1" in context_used
    assert "Doc 2" in context_used
    assert "Doc 3" in context_used
```

**Qué testear:**
- Que el contexto completo llegue de research a verify
- Que no se pierdan documentos en el camino
- Que la información relevante esté presente

---

### Pilar 7: Tiempos de ejecución (Performance Budget)

**¿Cada nodo termina dentro de un tiempo razonable?**

Cada nodo tiene un costo. Si uno se tarda demasiado, el usuario espera.

```python
# Ejemplo de problema:
# verify se tarda 30 segundos → usuario cierra la app

# Test que verifica esto:
def test_research_step_performance():
    """Verifica que research termina en menos de 5 segundos."""
    import time
    
    # GIVEN
    agent = ResearchAgent()
    agent.model = MagicMock()
    agent.model.invoke.return_value = MagicMock(content="respuesta")
    
    docs = [Document(page_content="test")]
    
    # WHEN
    start = time.time()
    result = agent.generate("test", docs)
    elapsed = time.time() - start
    
    # THEN
    assert elapsed < 5.0
```

**Qué testear:**
- Que cada nodo termine en tiempo aceptable
- Que el pipeline completo no exceda el presupuesto
- Que no haya timeouts innecesarios

---

### Pilar 8: Casos extremos (Edge Cases)

**¿El sistema maneja situaciones inusuales sin crashear?**

Los sistemas fallan en los bordes, no en el centro.

```python
# Ejemplo de problema:
# Pregunta vacía → el LLM recibe prompt vacío → error

# Test que verifica esto:
def test_empty_question_handled():
    """Verifica que preguntas vacías se manejan correctamente."""
    workflow = AgentWorkflow()
    workflow.relevance_checker = MagicMock()
    workflow.relevance_checker.check.return_value = RelevanceClassification.NO_MATCH
    
    state = {"question": "", "retriever": MagicMock()}
    result = workflow._check_relevance_step(state)
    
    assert result["is_relevant"] is False

def test_special_characters_in_question():
    """Verifica que caracteres especiales no crashean el sistema."""
    # GIVEN
    question = "¿Qué es ñoño? 🤔 Test: @#$%^&*()"
    
    checker = RelevanceChecker()
    checker.model = MagicMock()
    checker.model.invoke.return_value = MagicMock(content="NO_MATCH")
    
    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = [MagicMock()]
    
    # WHEN
    result = checker.check(question, mock_retriever)
    
    # THEN
    assert result == RelevanceClassification.NO_MATCH
```

**Qué testear:**
- Preguntas vacías
- Documentos vacíos
- Preguntas en idioma diferente
- Caracteres especiales: ñ, á, é, emojis
- Documentos de 1 página vs 500 páginas
- Misma pregunta 2 veces seguidas

---

## Prioridad de los pilares

```
1. Routing          → Si falla, todo lo demás no importa
2. Data Flow        → Si los formatos no coinciden, explota
3. Error Handling   → Si no maneja errores, crashea en producción
4. LLM Contract     → Los LLMs son impredecibles
5. Context          → Sin contexto correcto, las respuestas son malas
6. Edge Cases       → Los bordes son donde falla la gente
7. Performance      → Importante pero no crítico
8. State            → Ya cubierto parcialmente por los demás
```

---

## Estructura de carpetas

```
tests/
├── unit/                    # Pruebas unitarias
│   ├── test_agents.py
│   ├── test_document_processor.py
│   ├── test_retriever.py
│   ├── test_config.py
│   └── test_utils.py
├── integration/             # Pruebas de integración
│   ├── __init__.py
│   ├── test_document_processing.py
│   ├── test_workflow_routing.py      # Pilar 3: Routing
│   ├── test_data_flow.py             # Pilar 1: Data Flow
│   ├── test_error_handling.py        # Pilar 5: Error Handling
│   ├── test_llm_contract.py          # Pilar 4: LLM Contract
│   └── conftest.py                   # Fixtures compartidos
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
□ ¿Qué pilar de los 8 estoy atacando?
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

# Tests para DocChat

## Estructura

```
tests/
├── unit/               # Tests unitarios (sin dependencias externas)
│   ├── test_document_processor.py
│   ├── test_retriever.py
│   └── test_agents.py
├── integration/        # Tests de integración (con ChromaDB)
│   ├── test_pipeline.py
│   └── test_chromadb.py
├── pipeline/           # Tests del pipeline completo (con API)
│   └── test_full_flow.py
└── conftest.py         # Fixtures compartidos
```

## Ejecutar tests

```bash
# Solo unit (gratis, rápido)
pytest tests/unit/ -v

# Solo integración
pytest tests/integration/ -v

# Todos
pytest -v
```

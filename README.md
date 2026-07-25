# DocChat

> Multi-agent RAG system for document analysis using LangGraph and OpenRouter.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-412991?style=for-the-badge&logo=langchain&logoColor=white)
![OpenRouter](https://img.shields.io/badge/OpenRouter-DeepSeek-FF6B35?style=for-the-badge)
![Gradio](https://img.shields.io/badge/Gradio-5.x-FF7C00?style=for-the-badge&logo=gradio&logoColor=white)
![Docling](https://img.shields.io/badge/Docling-2.x-0066CC?style=for-the-badge)
![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5+-FFB300?style=for-the-badge)

---

## Overview

DocChat is a **multi-agent Retrieval Augmented Generation (RAG)** system that allows you to chat with your documents. Upload a PDF, DOCX, TXT, or MD file, ask a question, and get an AI-generated answer backed by the document content.

The system uses three specialized agents working in sequence:

1. **Relevance Checker** — Determines if the document can answer the question
2. **Research Agent** — Generates a draft answer from relevant document chunks
3. **Verification Agent** — Validates the answer against the source documents

## Workflow

![Agent Workflow](diagrama/workflow.png)

| Step | Agent | Description |
|------|-------|-------------|
| 1 | **Relevance Checker** | Classifies the document-question pair as `CAN_ANSWER`, `PARTIAL`, or `NO_MATCH` |
| 2 | **Research Agent** | Retrieves relevant chunks and generates a factual answer |
| 3 | **Verification Agent** | Cross-checks the answer for factual support, contradictions, and relevance |
| 4 | **Re-research** | If verification fails, the workflow loops back to step 2 |

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Gradio UI (app.py)                            │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  LangGraph Workflow                             │
│  ┌─────────────┐  ┌───────────┐  ┌───────────┐ │
│  │ Relevance   │→ │ Research  │→ │ Verifier  │ │
│  │ Checker     │  │ Agent     │  │ Agent     │ │
│  └─────────────┘  └───────────┘  └───────────┘ │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│  Hybrid Retriever (BM25 + ChromaDB)             │
│  Embeddings: qwen/qwen3-embedding-8b           │
└─────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| LLM | DeepSeek v3 (via OpenRouter) |
| Embeddings | Qwen3 Embedding 8B (via OpenRouter) |
| Vector Store | ChromaDB (local) |
| Retrieval | Hybrid BM25 + Semantic Search |
| Document Processing | Docling |
| Agent Framework | LangGraph |
| UI | Gradio |
| Structured Output | Pydantic |

## Project Structure

```
DocChat/
├── app.py                          # Gradio UI and entry point
├── generate_diagram.py             # Workflow diagram generator
├── requirements.txt
├── .env                            # API keys (not committed)
├── agents/
│   ├── models.py                   # Pydantic models (VerificationReport)
│   ├── relevance_checker.py        # Document-question relevance classifier
│   ├── research_agent.py           # Answer generation agent
│   ├── verification_agent.py       # Answer validation agent
│   └── workflow.py                 # LangGraph workflow orchestration
├── config/
│   ├── constants.py                # App constants
│   └── settings.py                 # Environment-based configuration
├── document_processor/
│   └── file_handler.py             # Document parsing and chunking
├── retriever/
│   └── builder.py                  # Hybrid retriever construction
├── diagrama/
│   └── workflow.mmd                # Mermaid workflow diagram
└── utils/
    └── logging.py                  # Loguru configuration
```

## Getting Started

### Prerequisites

- Python 3.11+
- An [OpenRouter API key](https://openrouter.ai/keys)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/DocChat.git
cd DocChat

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
echo 'OPENROUTER_API_KEY=your-api-key-here' > .env
```

### Running

```bash
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

## Configuration

All settings are in `config/settings.py` and can be overridden via `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | — | Required. Your OpenRouter API key |
| `CHAT_MODEL` | `deepseek/deepseek-chat` | LLM model for agents |
| `EMBEDDING_MODEL` | `qwen/qwen3-embedding-8b` | Embedding model |
| `VECTOR_SEARCH_K` | `10` | Number of chunks for vector search |
| `CACHE_EXPIRE_DAYS` | `7` | Document cache TTL |

## Supported Formats

- `.pdf`
- `.docx`
- `.txt`
- `.md`

## Cost

Using DeepSeek via OpenRouter, the cost per query is approximately **$0.0001 USD**.

## License

MIT

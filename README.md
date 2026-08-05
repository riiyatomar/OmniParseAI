# 📚 Document Chat Hub

A multi-page Streamlit application for chatting with **PDFs**, **CSVs**, and **ODF** documents using **Google Gemini AI**. Powered by RAG (Retrieval Augmented Generation), OCR, and FAISS vector search.

Also includes a **FastAPI REST API** (`app/main.py`) with versioned endpoints for headless ingestion and chat.

## ✨ Features

| Page            | Description                                                                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 📄 **PDF Chat** | Upload multiple PDFs, extract text (with OCR fallback for scanned docs), build a vector index, and ask questions with full conversation history. |
| 📊 **CSV Chat** | Upload a CSV and query its contents in plain English. Gemini analyses schema + data and returns structured answers.                              |
| 📝 **ODF Chat** | Upload LibreOffice / OpenDocument (`.odt`) files and chat with their content.                                                                    |

### Architecture Highlights

- **Modular backend** (`app/`) — config, LLM, parsers, services, and vector store in separate packages.
- **Shared styling & helpers** (`utils/styles.py`) — XSS-safe chat rendering, API key init, history controls.
- **Centralized config** (`app/core/config.py`) — all paths, model names, and settings in one place, overridable via `.env`.
- **Custom exceptions** (`app/core/exceptions.py`) — typed error hierarchy with HTTP status codes.
- **Retry / exponential backoff** for Gemini API calls.
- **Session-state vector store caching** — PDFs are only embedded once.
- **FastAPI REST API** with Swagger UI, API key auth, and versioned routes.
- **Cross-platform** — works on Windows, macOS, and Linux.

## 📁 Project Structure

```
pdf-chat-app/
├── app.py                        # Home page (Streamlit entry point)
├── requirements.txt              # Python dependencies
├── .env.example                  # Template for environment variables
├── .gitignore
├── README.md
│
├── app/                          # Modular backend
│   ├── core/
│   │   ├── config.py             # Pydantic settings (loaded from .env)
│   │   ├── exceptions.py         # Custom exception classes
│   │   └── security.py           # API key auth dependency
│   │
│   ├── llm/
│   │   ├── gemini.py             # Gemini API wrapper with retry
│   │   └── prompts.py            # Prompt templates (QA, CSV, ODF)
│   │
│   ├── parsers/
│   │   ├── base.py               # Abstract base parser + ParsedDocument
│   │   ├── pdf.py                # PyPDF2 + OCR fallback
│   │   ├── csv_parser.py         # Pandas CSV parser
│   │   ├── odf.py                # odfpy ODF parser
│   │   └── factory.py            # MIME-based parser routing
│   │
│   ├── services/
│   │   ├── chat.py               # RAG question answering
│   │   ├── ingestion.py          # File → parse → chunk → embed pipeline
│   │   └── file_manager.py       # Temp file handling + size validation
│   │
│   ├── vectorstore/
│   │   ├── embeddings.py         # Batched GoogleGenerativeAIEmbeddings
│   │   └── manager.py            # Session-isolated FAISS index management
│   │
│   ├── utils/
│   │   ├── cleaning.py           # Unicode normalization + garbage detection
│   │   └── chunking.py           # Prose and structured chunking strategies
│   │
│   ├── api/v1/
│   │   ├── router.py             # Aggregated v1 router
│   │   ├── deps.py               # Shared FastAPI dependencies
│   │   └── endpoints/
│   │       ├── health.py
│   │       ├── ingest.py
│   │       ├── chat.py
│   │       └── sessions.py
│   │
│   └── main.py                   # FastAPI app factory
│
├── pages/                        # Streamlit multi-page app
│   ├── 1_📄_PDF_Chat.py
│   ├── 2_📊_CSV_Chat.py
│   └── 3_📝_ODF_Chat.py
│
├── utils/
│   ├── __init__.py
│   └── styles.py                 # Shared CSS + helpers (render_chat_message, etc.)
│
└── .streamlit/
    └── config.toml               # Upload size limits, theme
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.9+**
- **Tesseract OCR** (for scanned PDFs)
- **Google Gemini API Key**

### Step 1 — Clone & Create Virtual Environment

```bash
git clone <your-repo-url>
cd pdf-chat-app

python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### Step 2 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Install Tesseract OCR

| OS          | Command                                                                                                                     |
| ----------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Windows** | Download from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki) and install to `C:\Program Files\Tesseract-OCR\` |
| **macOS**   | `brew install tesseract`                                                                                                    |
| **Linux**   | `sudo apt-get install tesseract-ocr`                                                                                        |

### Step 4 — Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API key:
# GOOGLE_API_KEY=your_key_here
```

> **Alternatively**, you can enter the API key directly in the app's sidebar.

### Step 5 — Run the App

**Streamlit UI:**

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

**FastAPI REST API:**

```bash
uvicorn app.main:app --reload --port 8000
```

Swagger UI at `http://localhost:8000/docs`.

## 🔑 Getting Your Google Gemini API Key

1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in → **Create API Key**
3. Copy and paste into `.env` or the app's sidebar

## ⚙️ Configuration

All settings are configurable via environment variables (or `.env` file). See `.env.example` for the full list:

| Variable                 | Default                | Description                    |
| ------------------------ | ---------------------- | ------------------------------ |
| `GOOGLE_API_KEY`         | —                      | Your Gemini API key            |
| `GEMINI_MODEL_NAME`      | `gemini-2.5-flash`     | Model for text generation      |
| `GEMINI_EMBEDDING_MODEL` | `models/embedding-001` | Model for embeddings           |
| `TESSERACT_CMD`          | Auto-detected          | Path to Tesseract binary       |
| `POPPLER_PATH`           | Auto-detected          | Path to Poppler (Windows only) |
| `CHUNK_SIZE`             | `1000`                 | Text chunk size for RAG        |
| `CHUNK_OVERLAP`          | `200`                  | Overlap between chunks         |
| `API_RETRY_ATTEMPTS`     | `3`                    | Max retries on API error       |

## 🛠️ Troubleshooting

| Issue                                      | Solution                                                                   |
| ------------------------------------------ | -------------------------------------------------------------------------- |
| `ModuleNotFoundError: google.generativeai` | `pip install -r requirements.txt`                                          |
| `TesseractNotFound`                        | Install Tesseract and set `TESSERACT_CMD` in `.env`                        |
| `API Key Error`                            | Verify key at [Google AI Studio](https://makersuite.google.com/app/apikey) |
| No text from PDF                           | Check if the PDF is image-only — OCR will be tried automatically           |

## 🔒 Security Best Practices

1. **Never commit API keys** — they belong in `.env` (gitignored).
2. **Use environment variables** in production.
3. **Rotate API keys** regularly.
4. **Monitor usage** in Google Cloud Console.

## 📊 Future Enhancements

- [ ] DOCX / TXT / PPTX support
- [ ] Multi-language OCR
- [ ] Persistent chat history (SQLite / PostgreSQL)
- [ ] Model selection dropdown
- [ ] Streaming responses

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

**Happy chatting with your documents! 📚✨**
.venv\Scripts\python.exe -m 
streamlit run app.py


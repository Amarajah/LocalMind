# LocalMind — Local AI Dev Assistant

> A self-hosted, browser-based coding assistant powered entirely by your local machine. No cloud APIs. No data egress. Your code never leaves your environment.

![Python](https://img.shields.io/badge/Python-3.13-3572A5?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-6.0-092E20?style=flat-square&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black?style=flat-square)

---

## What is LocalMind?

LocalMind is a web application that gives developers a clean, fast, VSCode-style interface to run AI coding assistance directly on their machine using [Ollama](https://ollama.com). It works for code-related tasks — without ever sending your code to an external server.

Every model runs locally. Every query stays local. The entire stack is containerised and self-hostable in minutes.

---

## Features

### Six Task Modes
Each mode applies a precisely engineered system prompt tuned for that specific task:

| Mode | What it does |
|---|---|
| 💬 **Chat** | Free-form coding conversation with full multi-turn history |
| 🔍 **Explain** | Breaks down any code snippet in plain English |
| 🧪 **Tests** | Generates a complete test file for any function or class |
| 📝 **Docstring** | Adds Google, NumPy, JSDoc, or PHPDoc documentation inline |
| 👁 **Review** | Structured code review: bugs, security, performance, style |
| 🔀 **PR Review** | Pastes a `git diff` and returns a full pull request review |

### Monaco Editor
The same editor engine that powers VSCode — syntax highlighting, language detection, multi-cursor, and `Cmd+Enter` to submit — embedded directly in the browser.

### Real-Time Streaming
Responses stream token by token via WebSockets (Django Channels). You see the model thinking in real time, and can stop generation at any point.

### Model Manager
Pull new Ollama models, delete installed ones, and monitor live system stats (RAM, CPU, disk, Ollama status) — all from the browser.

### Snippet Library
Save any AI response (along with the original source code) to a persistent library. Search, browse, view with syntax highlighting, and export as a file.

### Zero Data Egress
Verified: zero external network calls during normal operation. The only external dependency is Monaco Editor loaded from cdnjs on first page load.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0 (ASGI) |
| WebSockets | Django Channels 4.3 + Daphne |
| Channel Layer | In-memory (no Redis dependency for chat) |
| Database | PostgreSQL 15 |
| LLM Runtime | Ollama (runs on host, not in Docker) |
| LLM Client | `ollama` Python SDK 0.6 |
| Frontend | Django Templates + Tailwind CSS v3 |
| Code Editor | Monaco Editor 0.45 |
| Syntax Highlighting | highlight.js |
| Markdown Rendering | marked.js |
| System Stats | psutil |
| Containerisation | Docker + Docker Compose |
| Reverse Proxy | Nginx |
| Static Files | Whitenoise |

---

## Architecture

```
Browser
  │
  ├── HTTP requests ──► Nginx ──► Daphne (ASGI) ──► Django views
  │
  └── WebSocket ──────► Nginx ──► Daphne (ASGI) ──► Django Channels
                                                          │
                                                          ▼
                                               Ollama SDK (Python)
                                                          │
                                                          ▼
                                          Ollama (running on host Mac/Linux)
                                                          │
                                                          ▼
                                              Local LLM (gemma4, codellama, etc.)
```

**Key architecture decision:** Ollama runs directly on the host machine (not inside Docker) to access GPU/CPU natively. The Django container reaches it via `host.docker.internal:11434` on Mac/Windows, or `host-gateway` on Linux.

---

## Local Development Setup

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com/download) installed and running
- At least one model pulled: `ollama pull gemma4:e2b` or `ollama pull codellama:7b`
- Node.js (for Tailwind CSS build)

### 1. Clone the repository

```bash
git clone https://github.com/Amarajah/localmind.git
cd localmind
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and set your values:

```env
SECRET_KEY=your-secret-key-here        # generate with: python3 -c "import secrets; print(secrets.token_urlsafe(50))"
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=localai_db
POSTGRES_USER=localai_user
POSTGRES_PASSWORD=your-password-here

DATABASE_URL=postgresql://localai_user:your-password@db:5432/localai_db
REDIS_URL=redis://redis:6379/0
OLLAMA_HOST=http://host.docker.internal:11434

DB_HOST=db
DB_PORT=0000
```

### 3. Build the CSS

```bash
cd backend
npm install
npm run build:css
cd ..
```

### 4. Build and start containers

```bash
docker-compose up --build
```

### 5. Run migrations

```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py collectstatic --noinput
```

### 6. Open the app

```
http://localhost
```

---

## Project Structure

```
localmind/
├── backend/
│   ├── apps/
│   │   ├── assistant/              # Core AI logic
│   │   │   ├── consumers.py        # WebSocket consumer (streaming chat)
│   │   │   ├── ollama_client.py    # Ollama SDK integration layer
│   │   │   ├── prompts.py          # System prompts for all 6 task modes
│   │   │   ├── models.py           # ModelUsageLog, AppSettings
│   │   │   ├── views.py            # REST API: models, stats, settings
│   │   │   ├── urls.py             # API routes
│   │   │   └── routing.py          # WebSocket URL routing
│   │   └── snippets/               # Snippet library
│   │       ├── models.py           # Snippet model (with source_code field)
│   │       ├── views.py            # CRUD + export API
│   │       └── urls.py             # API routes
│   ├── config/
│   │   ├── settings.py             # Django settings
│   │   ├── urls.py                 # URL config + frontend page views
│   │   └── asgi.py                 # ASGI app with Channels routing
│   ├── templates/
│   │   ├── base.html               # Shared layout + sidebar navigation
│   │   ├── chat.html               # Main chat interface
│   │   ├── models.html             # Model manager
│   │   ├── snippets.html           # Snippet library
│   │   ├── pr_review.html          # PR review interface
│   │   └── settings.html           # App settings
│   ├── static/
│   │   └── css/
│   │       ├── input.css           # Tailwind source
│   │       └── output.css          # Compiled CSS (gitignored)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── tailwind.config.js
│   └── package.json
├── nginx/
│   ├── Dockerfile
│   └── nginx.conf                  # HTTP + WebSocket proxy config
├── .env.example
├── .gitignore
└── docker-compose.yml
```

---

## API Reference

### Assistant

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/assistant/models/` | List installed Ollama models |
| `POST` | `/api/assistant/models/pull/` | Pull a model (SSE stream) |
| `POST` | `/api/assistant/models/delete/` | Delete a model |
| `GET` | `/api/assistant/stats/` | System stats (RAM, CPU, disk, Ollama status) |
| `GET` | `/api/assistant/settings/` | Get app settings |
| `POST` | `/api/assistant/settings/update/` | Update app settings |
| `WS` | `/ws/chat/` | WebSocket streaming chat endpoint |

### WebSocket Message Protocol

**Client → Server:**
```json
{
  "type": "query",
  "mode": "explain | test | docstring | review | chat | pr_review",
  "code": "...your code or diff...",
  "language": "python",
  "model": "gemma4:e2b",
  "verbosity": "concise | detailed | step_by_step",
  "conversation_history": []
}
```

**Server → Client (streaming):**
```json
{ "type": "stream_start" }
{ "type": "token", "content": "Here" }
{ "type": "token", "content": " is" }
{ "type": "done", "total_chars": 1842, "duration_ms": 34521, "model": "gemma4:e2b" }
```

### Snippets

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/snippets/` | List snippets (supports `?q=search`) |
| `POST` | `/api/snippets/create/` | Save a snippet |
| `GET` | `/api/snippets/{id}/` | Get snippet detail |
| `PATCH` | `/api/snippets/{id}/` | Rename snippet |
| `DELETE` | `/api/snippets/{id}/` | Delete snippet |
| `GET` | `/api/snippets/{id}/export/` | Download as file |

---

## Recommended Models

| Model | Size | Best for |
|---|---|---|
| `gemma4:e2b` | 7.2GB | General coding, explanation, review |
| `codellama:7b` | 3.8GB | Code generation, completions |
| `deepseek-coder:6.7b` | 3.8GB | Code generation, tests |
| `qwen2.5-coder:7b` | 4.7GB | Multi-language coding tasks |
| `nomic-embed-text` | 274MB | Embeddings (not for chat) |

Pull any model from the Model Manager page or via terminal:
```bash
ollama pull codellama:7b
```

---

## Privacy

LocalMind is designed for environments where code privacy is non-negotiable:

- **Zero external API calls** during normal operation
- **No telemetry** — no usage data sent anywhere
- **No authentication required** — designed for single-developer local use
- **All data stays on your machine** — PostgreSQL runs in Docker, files stay local
- Verify yourself: open Chrome DevTools → Network tab → filter by "external" — you'll see nothing during a chat session

---

## Built With

This project was built as part of a deliberate portfolio engineering practice — every architectural decision documented, every trade-off considered. Key decisions:

- **Daphne over Gunicorn** — ASGI required for WebSocket support; Daphne is the canonical Django Channels server
- **In-memory channel layer over Redis** — single-user tool; Redis channel layer adds latency and complexity with no benefit for direct 1-to-1 WebSocket connections
- **Ollama on host, Django in Docker** — GPU/CPU access requires native process; `host.docker.internal` bridges the network boundary cleanly
- **Monaco over CodeMirror** — feature parity with VSCode; better language support and keyboard shortcuts out of the box
- **SSE for model pull progress, WebSocket for chat** — pull is one-directional server push; WebSocket bidirectionality is only needed for the interactive chat loop

---
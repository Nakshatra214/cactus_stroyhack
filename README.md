# StoryHack: Agentic Video Editor 🎬

> **Hackathon Project** — AI-powered platform that converts research papers, lecture notes, and reports into editable, scene-based videos with human-in-the-loop editing.

## 🏗️ Architecture

```
Upload Content → Script Generation → Scene Segmentation → Visual Generation
→ Voice Narration → Video Assembly → Scene Editing UI → Partial Regeneration → Export
```

### Multi-Agent System

| Agent | Role |
|-------|------|
| **Script Agent** | Summarizes content, generates scene-based video scripts |
| **Visual Agent** | Creates images/illustrations for each scene (Stability AI) |
| **Voice Agent** | Generates voiceover narration (OpenAI TTS) |
| **Fact-Check Agent** | Validates scripts against source, provides confidence scores |

## 🛠️ Tech Stack

- **Frontend:** Next.js 14, React, TailwindCSS, Zustand
- **Backend:** Python FastAPI, SQLAlchemy (async)
- **AI:** OpenAI GPT-4, LangChain, Stability AI
- **Video:** MoviePy, FFmpeg
- **Database:** PostgreSQL
- **Queue:** Redis + Celery

## 📁 Project Structure

```
cactus_storyhack/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py             # Settings & env vars
│   ├── agents/               # AI agents (script, visual, voice, factcheck)
│   ├── routers/              # API endpoints
│   ├── services/             # Business logic
│   ├── video/                # MoviePy video processing
│   ├── database/             # SQLAlchemy models & DB setup
│   └── tasks/                # Celery background tasks
├── frontend/
│   ├── app/                  # Next.js pages (upload, editor)
│   ├── components/           # React components
│   └── lib/                  # Zustand store, API client
├── scripts/                  # Setup & run scripts
├── docker-compose.yml        # PostgreSQL + Redis
└── .env.example              # Environment template
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Docker** (for PostgreSQL and Redis)
- **FFmpeg** (for video processing)

### 1. Clone & Setup

```bash
# Clone the repository
git clone <repo-url>
cd cactus_storyhack

# Copy environment template
cp .env.example backend/.env
# Edit backend/.env and add your API keys (optional — system works with mock data)
```

### 2. Start Database Services

```bash
docker-compose up -d
```

### 3. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 5. Open the App

- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs

### Windows Quick Start

```bash
scripts\setup_env.bat
scripts\run_server.bat
```

## 🔑 API Keys (Optional)

The system works **without API keys** using mock/placeholder data. Add keys for full AI features:

| Key | Purpose | Get it from |
|-----|---------|-------------|
| `OPENAI_API_KEY` | Script generation + TTS | [platform.openai.com](https://platform.openai.com) |
| `STABILITY_API_KEY` | Image generation | [stability.ai](https://stability.ai) |
| `ELEVENLABS_API_KEY` | Premium voice (optional) | [elevenlabs.io](https://elevenlabs.io) |

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload_content` | Upload PDF/DOCX/text |
| POST | `/api/generate_script` | Generate video script |
| POST | `/api/generate_scenes` | Create scene records |
| POST | `/api/generate_visuals` | Generate scene images |
| POST | `/api/generate_voice` | Generate voiceovers |
| POST | `/api/build_video` | Build & merge video |
| POST | `/api/edit_scene` | Edit scene content |
| POST | `/api/regenerate_scene` | Regenerate single scene |
| GET  | `/api/export_video/{id}` | Download final video |
| GET  | `/api/scenes/{id}` | Get project scenes |
| GET  | `/api/scene_versions/{id}` | Get scene version history |
| POST | `/api/revert_scene` | Revert to previous version |
| POST | `/api/reorder_scenes` | Drag-and-drop reordering |

## ✨ Key Features

- **Scene-Level Editing** — Edit script, visuals, voice for individual scenes
- **Partial Regeneration** — Only rebuild edited scenes, not the entire video
- **Explainability Panel** — Source references + confidence scores for every scene
- **Version Control** — Full scene history with one-click revert
- **Drag-and-Drop** — Reorder scenes in the timeline
- **Export** — Download as MP4

## 📄 License

Built for StoryHack Hackathon 2026.

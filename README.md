# 🎬 FlickFind — AI-Powered Mood & Conversational Cinema Concierge

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg?style=flat&logo=react&logoColor=black)](https://react.dev)
[![pgvector](https://img.shields.io/badge/pgvector-PostgreSQL%2015-336791.svg?style=flat&logo=postgresql&logoColor=white)](https://github.com/pgvector/pgvector)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-3.5%20Flash-4285F4.svg?style=flat&logo=google&logoColor=white)](https://ai.google.dev)
[![Vite](https://img.shields.io/badge/Vite-5+-646CFF.svg?style=flat&logo=vite&logoColor=white)](https://vitejs.dev)

> **FlickFind** is a next-generation movie recommendation platform that replaces rigid genre filters with an intuitive, conversational AI concierge. It pairs a **Dual-Pass LLM pipeline** (powered by Google Gemini) with a **768-dimensional pgvector semantic search engine** querying a catalog of over **1,000,000 movies** in milliseconds.

---

## 📑 Table of Contents
- [System Architecture](#-system-architecture)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start Guide](#-quick-start-guide)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Environment Configuration](#2-environment-configuration)
  - [3. Start PostgreSQL + pgvector](#3-start-postgresql--pgvector)
  - [4. Backend Setup & Seeding](#4-backend-setup--seeding)
  - [5. Frontend Setup](#5-frontend-setup)
- [API Reference](#-api-reference)
- [Engineering Highlights](#-engineering-highlights)
- [License](#-license)

---

## 🏛 System Architecture

```mermaid
flowchart TD
    User([User in React UI]) -->|Natural Language Prompt & History| Frontend[React + Vite Frontend]
    Frontend -->|POST /api/v1/recommend/mood| FastAPI[FastAPI Backend Engine]

    subgraph Backend Pipeline
        FastAPI --> Pass1[Pass 1: Gemini Context Compiler]
        Pass1 -->|Dense Search Query| Embedder[768-dim Vector Embedder nomic-ai]
        Embedder -->|Query Vector| PgVector[(PostgreSQL + pgvector\n1M+ Films Catalog)]
        
        PgVector -->|Cosine Distance + Metadata Filters| CandidatePool[Filtered Candidate Pool\n35 Diverse Candidates]
        
        FastAPI -->|User History / Taste Profile| PersonaEngine[Dynamic Persona Vector]
        PersonaEngine -.->|Blended Vector Scoring| CandidatePool

        CandidatePool --> Pass2[Pass 2: Gemini Concierge Selector]
        Pass2 -->|Curated 5 Films + Hybrid Summaries| StructuredJSON[Validated Pydantic Payload]
    end

    StructuredJSON -->|Response JSON| Frontend
    Frontend --> User
```

---

## ✨ Key Features

- **🧠 Dual-Pass LLM Intelligence**:
  - **Pass 1 (Compiler)**: Analyzes conversational history, user mood, and nuance to construct a dense semantic search paragraph and determine if the user wants to break away from their profile.
  - **Pass 2 (Concierge)**: Evaluates candidates fetched from PostgreSQL, filters out noise, and writes custom non-spoiler hybrid summaries tailored to the conversation.
- **🔍 Sub-Second Semantic Search over 1,000,000+ Movies**:
  - Employs 768-dimensional embeddings generated with `nomic-ai/nomic-embed-text-v1.5` mapped directly into PostgreSQL `vector(768)` columns.
- **⚡ Resilient Gemini Model Cascade**:
  - Built-in automatic fallback: tries `gemini-3.5-flash-lite`, then cascades to `gemini-3.5-flash`, `gemini-flash-latest`, and `gemini-3.8-flash` to gracefully withstand high-demand spikes (HTTP 503) or API updates.
- **👤 Dynamic Long-Term Persona Learning**:
  - **Watched films**: Persona vector is shifted 15% toward watched movie vectors via Exponential Moving Average (EMA).
  - **Disliked films**: Persona vector applies penalty repulsion away from user rejection reasons.
  - **Gamified Watcher Tiers**: Users progress from `BASIC_WATCHER` (0-4) to `DEEP_DIVER` (5-14) and `CRITIC` (15+).
- **🛡 Anti-Echo Tracking**:
  - The UI tracks currently displayed movie IDs and instructs pgvector to exclude them on subsequent dialogue turns so the user never receives repetitive recommendations.
- **🔀 Dynamic Profile Override**:
  - If a user usually watches sci-fi but asks for *"something lighthearted for date night"*, the AI automatically bypasses profile constraints for that turn.

---

## 🛠 Tech Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 18, Vite, Tailwind CSS, Heroicons / Lucide, Fetch API |
| **Backend** | Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy, Uvicorn |
| **AI / NLP** | Google Gemini (`google-genai` SDK), SentenceTransformers (`nomic-ai/nomic-embed-text-v1.5`), PyTorch |
| **Database** | PostgreSQL 15, `pgvector` extension, Psycopg2 |
| **Containerization** | Docker, Docker Compose |
| **Security** | Passlib, Bcrypt + SHA-256 pre-hashing (preventing 72-byte truncation) |

---

## 📂 Project Structure

```text
FlickFind/
├── docker-compose.yml          # PostgreSQL 15 + pgvector container definition
├── README.md                   # Complete system documentation
├── .gitignore                  # Git rules protecting secrets and multi-GB parquet assets
├── backend/
│   ├── .env.example            # Environment variables template
│   ├── requirements.txt        # Python backend dependencies
│   ├── main.py                 # FastAPI application & recommendation routing
│   ├── ai_service.py           # 768-dim Vector embedding service (Nomic + Gemini fallback)
│   ├── database.py             # SQLAlchemy session and engine management
│   ├── models.py               # Database schemas (User, Movie, Watchlist, History)
│   ├── schemas.py              # Pydantic validation models
│   ├── auth_utils.py           # Bcrypt salted password hashing with SHA-256 pre-hash
│   ├── init_db.py              # Database reset / migration script
│   ├── seed_db.py              # Targeted testing catalog seeder (protected against data loss)
│   └── bulk_seed.py            # High-throughput batch streaming seeder for 1M+ parquet records
└── frontend/
    ├── package.json            # Node.js dependencies
    ├── vite.config.js          # Vite bundler configuration
    ├── index.html              # HTML5 entrypoint
    ├── src/
    │   ├── main.jsx            # React root mount
    │   ├── App.jsx             # Main conversational interface & state management
    │   ├── App.css             # Glassmorphism & custom styling
    │   ├── index.css           # Tailwind base directives
    │   └── components/
    │       ├── MovieCard.jsx   # Interactive film card with trailer & reaction actions
    │       └── WatchlistModal.jsx # Saved film manager
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
Ensure you have the following installed:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Python 3.10+](https://www.python.org/)
- [Node.js 18+](https://nodejs.org/)
- A free [Google Gemini API Key](https://aistudio.google.com/)

---

### 2. Environment Configuration

Create a `.env` file inside the `backend/` directory:

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` with your API credentials:
```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://flickadmin:flicksecretpassword@127.0.0.1:5433/flickfind_db
USE_GEMINI_EMBEDDINGS=false
```

---

### 3. Start PostgreSQL + pgvector

From the project root:
```bash
docker-compose up -d
```
Verify the container is healthy:
```bash
docker ps
# Status should show 'flickfind_postgres' running on port 5433 -> 5432
```

---

### 4. Backend Setup & Seeding

1. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Seed the database**:
   - **Quick Start (Sample Catalog)**:
     ```bash
     python seed_db.py
     ```
   - **Full Catalog (1,000,000+ Movies from Parquet)**:
     Place `movies_raw.parquet` in `backend/` and run:
     ```bash
     python bulk_seed.py
     ```

3. **Start the API Server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   Check health at: [http://127.0.0.1:8000/api/v1/health/db](http://127.0.0.1:8000/api/v1/health/db)

---

### 5. Frontend Setup

1. **Install packages & start dev server**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

2. **Open the App**:
   Navigate to [http://localhost:5173](http://localhost:5173) in your browser.

---

## 📡 API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API status check |
| `GET` | `/api/v1/health/db` | Health check & total count of indexed movies |
| `POST` | `/api/v1/auth/register` | Register new account (`username`, `email`, `password`) |
| `POST` | `/api/v1/auth/login` | Authenticate user session |
| `POST` | `/api/v1/recommend/mood` | **Main recommendation engine** (processes conversation & returns 5 movies) |
| `POST` | `/api/v1/user/watchlist` | Toggle film in/out of user's personal watchlist |
| `GET` | `/api/v1/user/watchlist/{user_id}` | Fetch all watchlisted films for a user |
| `POST` | `/api/v1/user/watched` | Log watched movie, rating, review & trigger persona vector update |
| `POST` | `/api/v1/user/dislike` | Flag movie with rejection reason & apply persona vector penalty |

---

## 💡 Engineering Highlights

### 1. Vector Space Alignment & transformers 5.x Patch
When upgrading to modern HuggingFace `transformers >= 4.45 / 5.x`, legacy `NomicBERT` code failed due to the removal of `PreTrainedModel.get_extended_attention_mask`. FlickFind implements a backward-compatibility patch directly in `ai_service.py`, allowing `nomic-ai/nomic-embed-text-v1.5` to run natively on the newest Python and transformers releases without requiring downgrades. This preserves 100% semantic coordinate alignment with the 1M+ pre-computed movie vectors stored in pgvector.

### 2. High-Demand Resilience (Model Cascade)
Google Gemini models occasionally experience temporary traffic spikes resulting in HTTP 503 (`UNAVAILABLE`) responses. Rather than returning a 500 error to the client, FlickFind executes an automated model fallback cascade (`gemini-3.5-flash-lite` ➔ `gemini-3.5-flash` ➔ `gemini-flash-latest` ➔ `gemini-3.8-flash`), delivering uninterrupted uptime.

### 3. Accidental Overwrite Protection
`seed_db.py` contains automated record detection: if the database already contains records (e.g. the 1M+ warehouse catalog), it safely halts execution unless explicitly invoked with `--force`, safeguarding production data.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).

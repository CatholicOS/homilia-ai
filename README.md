# Homilia— AI Chatbot for Catholic Parishes

Homilia is an AI-powered Q&A platform for Catholic parishes.  
Pastors can upload homilies, bulletins, and other church documents, and parishioners can ask natural-language questions about parish life, homilies, or announcements.

The chatbot uses retrieval-augmented generation (RAG) to provide contextual answers from parish-specific data.

---

## Tech Stack

### Backend
- FastAPI — Python API framework  
- PostgreSQL — relational database (users, parishes, docs, chat logs)  
- Amazon S3 — file storage for uploads  
- OpenSearch — semantic and keyword document retrieval  
- Strands SDK — for LLM orchestration (chat generation)

### Frontend
- React — modern SPA frontend  
- Vite — build tool for fast dev & bundling  
- TailwindCSS — styling system

---

## Features

### For Parishioners
- Choose your parish and chat with an AI trained on your parish’s homilies & bulletins
- Ask about recent sermons, parish news, or upcoming events

### For Pastors/Admins
- Upload homilies, bulletins, or announcements (PDF, DOCX, etc.)
- Automatic ingestion and indexing of text for contextual search
- Manage multiple parishes and document histories

---

## Project Structure (tentative)

```
backend/
│
├── app/
│   ├── main.py                 # FastAPI entrypoint
│   ├── core/
│   │   ├── config.py           # Environment variables and app settings
│   │   └── security.py         # JWT creation/validation
│   ├── db/
│   │   ├── database.py         # SQLAlchemy engine + session
│   │   ├── models.py           # ORM models (User, Parish, Document, ChatLog)
│   │   └── schemas.py          # Pydantic schemas for API I/O
│   ├── routes/
│   │   ├── auth.py             # Signup/login endpoints
│   │   ├── parishes.py         # Parish listing and retrieval
│   │   ├── documents.py        # File upload & ingestion
│   │   ├── chat.py             # AI chat endpoints (RAG)
│   │   └── feedback.py         # User feedback collection
│   ├── services/
│   │   ├── ingestion.py        # Text extraction, chunking, embedding
│   │   └── search.py           # OpenSearch utilities
│   └── utils/
│       └── s3.py               # S3 upload/download helpers
│
└── requirements.txt

frontend/
│
├── src/
│   ├── components/             # Reusable UI elements
│   ├── pages/                  # Auth, Chat, Admin pages
│   ├── hooks/                  # Custom React hooks
│   └── services/               # API client for FastAPI backend
└── package.json
```

---

## Setup Instructions

### 1. Clone the repo

```
git clone https://github.com/CatholicOS/homilia-ai.git
cd homilia-ai
```

---

### 2. Backend Setup

#### Create a virtual environment
```
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

#### Install dependencies
```
pip install -r requirements.txt
```

#### Configure environment variables

Create `.env` in `backend/`:

```
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/parishchat
S3_BUCKET_NAME=your-s3-bucket
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
OPENSEARCH_URL=https://your-opensearch-endpoint
JWT_SECRET=supersecret
STRANDS_API_KEY=your-strands-api-key
```

#### Run database migrations
```
alembic upgrade head
```

#### Start the backend server
```
uvicorn app.main:app --reload
```

---

### 3. Frontend Setup

```
cd frontend
npm install
npm run dev
```

The app will start on http://localhost:####

---

## Core API Endpoints (planned)

| Method | Route | Description |
|--------|--------|-------------|
| POST | /auth/signup | Create a new user |
| POST | /auth/login | Login and receive JWT |
| GET  | /parishes | List available parishes |
| GET  | /parishes/{id} | Get parish details |
| POST | /documents/upload | Upload parish document |
| GET  | /documents/{parish_id} | List parish documents |
| POST | /chat | Ask a question to the AI |
| POST | /feedback | Submit chat feedback |

---

## Database Entities

| Table | Purpose |
|--------|----------|
| users | Parishioners & pastors; stores credentials and roles |
| parishes | Parish metadata (name, slug, location) |
| documents | Uploaded parish files (homilies, bulletins) |
| chunks | Extracted text chunks for retrieval |
| chat_logs | User chat sessions and messages |
| feedback | User feedback on chat responses |

---

## Development Notes

- Document ingestion runs synchronously for now (no Redis)
- OpenSearch is used for retrieval; embeddings stored directly in vector fields
- Authentication handled via JWT; no session store required for MVP
- S3 handles file storage; Postgres stores references + metadata

---

## Roadmap

- [ ] Basic FastAPI backend with RAG
- [ ] Parish and user management
- [ ] File upload and text ingestion
- [ ] Vector embedding & semantic search integration
- [ ] Full admin dashboard
- [ ] Chat streaming and feedback dashboard
- [ ] Redis integration for async jobs (optional)
- [ ] Multi-language support

---

## Contributing

Pull requests welcome.  
Please follow standard PEP8 and Prettier formatting guidelines.

---


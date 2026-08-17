# NyayaAI Law Assistance Backend

Backend service powered by FastAPI, SQLAlchemy, Alembic, and Anthropic Claude-3.5 for providing automated legal assistance, academy content, document parsing, and quizzes.

## Project Structure

```
law_assistance_backend/
├── app/
│   ├── main.py                 # FastAPI Application Entrypoint
│   ├── core/                   # Security, configuration, exceptions, logging
│   ├── api/                    # API Routing and V1 Endpoints
│   ├── models/                 # Database Models (SQLAlchemy)
│   ├── schemas/                # Data Schemas (Pydantic)
│   ├── services/               # Business Logic Services
│   ├── repositories/           # Repository Pattern (CRUD operations)
│   ├── db/                     # DB session, initialization, base metadata
│   ├── ai/                     # AI Prompts, Retrievers, Vector Store & LLM Client
│   ├── middleware/             # Rate Limiter, CORS, Auth Custom Middleware
│   └── utils/                  # Validators, text splitter, PDF parser
├── alembic/                    # DB Migrations Setup
├── tests/                      # Pytest unit tests
└── scripts/                    # Ingestion and seeding helper scripts
```

## Setup Instructions

1. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   ```

2. **Activate Virtual Environment**:
   * Windows:
     ```bash
     venv\Scripts\activate
     ```
   * Linux/macOS:
     ```bash
     source venv/bin/activate
     ```

3. **Install Dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Copy `.env.example` to `.env` and fill in custom configurations:
   ```bash
   cp .env.example .env
   ```

5. **Run Database Migrations** (if DB is configured):
   ```bash
   alembic upgrade head
   ```

6. **Run Local Dev Server**:
   ```bash
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`. You can access documentation at `/docs` or `/redoc`.

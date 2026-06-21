# Local Development

## 1. Clone the Repository

```bash
git clone https://github.com/mars01hash/nlp-customer-support-bangla.git
cd nlp-customer-support-bangla
```

## 2. Backend Setup

```bash
cd backend
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS / Linux

pip install -r requirements.txt
```

Copy the environment file and configure your LLM provider:

```bash
cp .env.example .env
# Edit .env and set LLM_PROVIDER + LLM_API_KEY
```

Start the API server:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload
```

!!! success "Backend ready"
    - API: [http://localhost:8090](http://localhost:8090)
    - Swagger docs: [http://localhost:8090/docs](http://localhost:8090/docs)

On first run the backend automatically:

- Creates all database tables
- Seeds demo tenants, users, and products
- Populates the ChromaDB FAQ vector store

## 3. Frontend Setup

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

!!! success "Frontend ready"
    - App: [http://localhost:5173](http://localhost:5173)

## 4. Verify

Try logging in with one of the [pre-seeded accounts](../accounts.md). The login page auto-routes to the correct dashboard based on role.

## Logs

Both servers write logs to the project root when started via the helper script:

| File | Contents |
|---|---|
| `backend.log` | FastAPI + LangGraph agent trace |
| `frontend.log` | Vite dev server output |

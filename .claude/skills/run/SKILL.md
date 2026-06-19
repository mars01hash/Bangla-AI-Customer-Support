---
description: Launch the full Bangla AI Customer Support app locally — FastAPI backend on port 8090 and Vite frontend on port 5173. Use this for any task that needs the live app running.
---

# Run — Local Dev Stack

Starts the FastAPI backend (port 8090) and the React/Vite frontend (port 5173) as background processes.

## Prerequisites

- Python 3.10+ with `venv` already created at `backend/venv/`
- Node.js 18+ with `npm` on PATH
- Working directory: project root (`H:\nlp-customer-support-bangla`)

If the venv doesn't exist yet:
```powershell
cd backend
python -m venv venv
venv\Scripts\pip install -r requirements.txt
cd ..
```

If `node_modules` is missing:
```powershell
cd frontend
npm install
cd ..
```

## Run

Launch both servers via the helper script:

```powershell
powershell -ExecutionPolicy Bypass -File .claude\skills\run\start.ps1
```

Or start them individually:

**Backend:**
```powershell
Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd 'H:\nlp-customer-support-bangla\backend'; venv\Scripts\activate; uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload *> '..\backend.log'"
```

**Frontend:**
```powershell
Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd 'H:\nlp-customer-support-bangla\frontend'; npm run dev *> '..\frontend.log'"
```

## Verify readiness

Wait for both servers then hit the health endpoint:

```powershell
# Backend ready check (up to 30s)
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
    try { $r = Invoke-WebRequest -Uri 'http://localhost:8090/' -UseBasicParsing -TimeoutSec 2; $ok = $true; break } catch {}
    Start-Sleep 1
}
if (-not $ok) { Write-Error "Backend did not start in 30s"; exit 1 }

# Frontend ready check (up to 30s)
$ok = $false
for ($i = 0; $i -lt 30; $i++) {
    try { $r = Invoke-WebRequest -Uri 'http://localhost:5173/' -UseBasicParsing -TimeoutSec 2; $ok = $true; break } catch {}
    Start-Sleep 1
}
if (-not $ok) { Write-Error "Frontend did not start in 30s"; exit 1 }

Write-Output "Both servers are up."
```

Or check logs directly:
```powershell
Get-Content backend.log -Tail 20
Get-Content frontend.log -Tail 10
```

## URLs

| Service | URL |
|---|---|
| Customer chat (React UI) | http://localhost:5173 |
| API Swagger docs | http://localhost:8090/docs |
| Health check | http://localhost:8090/ |

## Pre-seeded accounts

| Role | Email | Password |
|---|---|---|
| Admin | admin@example.com | adminpassword123 |
| Agent | agent@example.com | agentpassword123 |
| Customer | customer@example.com | customerpassword123 |

## Stop

```powershell
# Kill by port
Stop-Process -Id (Get-NetTCPConnection -LocalPort 8090 -ErrorAction SilentlyContinue).OwningProcess -Force -ErrorAction SilentlyContinue
Stop-Process -Id (Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue).OwningProcess -Force -ErrorAction SilentlyContinue
```

## Environment variables

The backend reads from `backend/.env` (optional — defaults work for local dev):

| Variable | Default | Notes |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./support_platform.db` | Switch to Postgres for prod |
| `LLM_PROVIDER` | `mock` | `openai`, `groq`, or `huggingface` for real LLM |
| `LLM_API_KEY` | `mock-key` | API key for chosen provider |
| `JWT_SECRET` | hardcoded default | Change in production |
| `CHROMA_PERSIST_DIRECTORY` | `./chroma_db` | Vector store path |

## Logs

- Backend: `backend.log` in project root
- Frontend: `frontend.log` in project root

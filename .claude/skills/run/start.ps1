# Starts backend (port 8090) and frontend (port 5173) in separate windows.
# Run from project root: powershell -ExecutionPolicy Bypass -File .claude\skills\run\start.ps1

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

Write-Host "Starting FastAPI backend on port 8090..."
Start-Process powershell -ArgumentList '-NoExit', '-Command', @"
cd '$root\backend'
venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8090 --reload *>> '$root\backend.log'
"@

Start-Sleep 2

Write-Host "Starting Vite frontend on port 5173..."
Start-Process powershell -ArgumentList '-NoExit', '-Command', @"
cd '$root\frontend'
npm run dev *>> '$root\frontend.log'
"@

Write-Host ""
Write-Host "Servers launching. Check:"
Write-Host "  Frontend : http://localhost:5173"
Write-Host "  API docs : http://localhost:8090/docs"
Write-Host "  Logs     : backend.log / frontend.log"

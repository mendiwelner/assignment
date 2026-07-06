# Helper: run backend from project root with PYTHONPATH set
$env:PYTHONPATH = Join-Path -Path $PSScriptRoot -ChildPath 'backend'
& .\.venv\Scripts\python.exe -m uvicorn backend.app.main:create_app --factory --host 0.0.0.0 --port 8000

@echo off
SET PYTHONPATH=%~dp0backend
"%~dp0\.venv\Scripts\python.exe" -m uvicorn backend.app.main:create_app --factory --host 0.0.0.0 --port 8000

@echo off
cd /d %~dp0
echo Iniciando FastAPI con Uvicorn...
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause

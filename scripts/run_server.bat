@echo off
echo ============================================
echo  StoryHack: Starting Development Servers
echo ============================================

:: Start backend
echo [1/3] Starting FastAPI backend...
start "StoryHack Backend" cmd /k "cd backend && call venv\Scripts\activate && uvicorn main:app --host 0.0.0.0 --port 8000"

:: Wait a bit
ping -n 3 127.0.0.1 >nul

:: Start Celery
echo [2/3] Starting Celery worker...
start "StoryHack Celery" cmd /k "cd backend && call venv\Scripts\activate && celery -A tasks.celery_app worker --loglevel=info -P gevent"

:: Wait for backend
ping -n 3 127.0.0.1 >nul

:: Start frontend
echo [3/3] Starting Next.js frontend...
start "StoryHack Frontend" cmd /k "cd frontend && npm.cmd run dev"

echo ============================================
echo  Backend:  http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo  Frontend: http://localhost:3000
echo ============================================

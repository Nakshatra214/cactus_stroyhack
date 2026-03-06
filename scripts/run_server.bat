@echo off
echo ============================================
echo  StoryHack: Starting Development Servers
echo ============================================

:: Start backend
echo [1/2] Starting FastAPI backend...
start "StoryHack Backend" cmd /k "cd backend && call venv\Scripts\activate && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

:: Wait for backend
timeout /t 3 /nobreak >nul

:: Start frontend
echo [2/2] Starting Next.js frontend...
start "StoryHack Frontend" cmd /k "cd frontend && npm run dev"

echo ============================================
echo  Backend:  http://localhost:8000
echo  API Docs: http://localhost:8000/docs
echo  Frontend: http://localhost:3000
echo ============================================

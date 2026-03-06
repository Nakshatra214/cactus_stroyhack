@echo off
echo ============================================
echo  StoryHack: Environment Setup (Windows)
echo ============================================

:: Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop.
    exit /b 1
)

:: Start services
echo [1/4] Starting PostgreSQL and Redis...
docker-compose up -d

:: Backend setup
echo [2/4] Setting up backend...
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate
pip install -r requirements.txt
cd ..

:: Frontend setup
echo [3/4] Setting up frontend...
cd frontend
call npm install
cd ..

:: Environment file
echo [4/4] Checking .env file...
if not exist backend\.env (
    copy .env.example backend\.env
    echo Created backend\.env from template. Please add your API keys!
)

echo ============================================
echo  Setup complete!
echo  Run: scripts\run_server.bat
echo ============================================

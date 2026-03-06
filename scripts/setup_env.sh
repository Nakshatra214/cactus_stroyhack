#!/bin/bash
echo "============================================"
echo " StoryHack: Environment Setup"
echo "============================================"

# Start services
echo "[1/4] Starting PostgreSQL and Redis..."
docker-compose up -d

# Backend setup
echo "[2/4] Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..

# Frontend setup
echo "[3/4] Setting up frontend..."
cd frontend
npm install
cd ..

# Environment file
echo "[4/4] Checking .env file..."
if [ ! -f backend/.env ]; then
    cp .env.example backend/.env
    echo "Created backend/.env from template. Please add your API keys!"
fi

echo "============================================"
echo " Setup complete!"
echo " Run: scripts/run_server.sh"
echo "============================================"

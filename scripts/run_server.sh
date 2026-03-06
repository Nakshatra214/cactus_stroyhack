#!/bin/bash
echo "============================================"
echo " StoryHack: Starting Development Servers"
echo "============================================"

# Start backend
echo "[1/2] Starting FastAPI backend..."
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait for backend
sleep 3

# Start frontend
echo "[2/2] Starting Next.js frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "============================================"
echo " Backend:  http://localhost:8000"
echo " API Docs: http://localhost:8000/docs"
echo " Frontend: http://localhost:3000"
echo "============================================"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait

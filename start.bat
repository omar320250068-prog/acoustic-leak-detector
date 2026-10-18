@echo off
title Acoustic Leak Detector — Launcher

echo Starting Backend API...
start "Backend Server" cmd /k "cd backend && python main.py"

echo Waiting for backend to initialize...
timeout /t 3 /nobreak >nul

echo Starting Sensor Simulator...
start "Sensor Simulator" cmd /k "cd backend && python simulator.py"

echo Launching Frontend Dashboard...
cd frontend
start http://localhost:8080
python -m http.server 8080

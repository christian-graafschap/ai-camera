@echo off
cd /d "%~dp0"
.\.venv\Scripts\python.exe dashboard.py model=yolo26n.pt source=0

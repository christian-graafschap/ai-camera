@echo off
setlocal
cd /d "%~dp0"

echo === AI-Camera setup ===

rem Zoek een Python-interpreter: eerst de py-launcher met 3.11, anders python op PATH
set "PY="
py -3.11 --version >nul 2>&1 && set "PY=py -3.11"
if not defined PY (
    python --version >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo [FOUT] Geen Python gevonden. Installeer Python 3.11 via https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Gebruik: %PY%
%PY% --version

rem Maak de venv aan als die nog niet bestaat
if exist ".venv\Scripts\python.exe" (
    echo .venv bestaat al, wordt hergebruikt.
) else (
    echo Virtualenv aanmaken in .venv ...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [FOUT] Aanmaken van de venv is mislukt.
        pause
        exit /b 1
    )
)

echo Pip bijwerken ...
.\.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto :fout

echo Packages installeren ...
rem ultralytics trekt torch, torchvision, opencv-python, numpy en pillow mee
rem pygrabber is nodig voor camera's.py (lijst van DirectShow-camera's)
.\.venv\Scripts\python.exe -m pip install ultralytics pygrabber
if errorlevel 1 goto :fout

echo.
echo === Setup klaar. Start de camera met start-camera.bat ===
pause
exit /b 0

:fout
echo [FOUT] Installatie van packages is mislukt.
pause
exit /b 1

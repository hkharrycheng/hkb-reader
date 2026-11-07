@echo off
REM HKBReader local prototype server (port 8790)
REM Double-click this file, then open http://127.0.0.1:8790/index.html
cd /d "%~dp0"
start "HKBReader server" python -m http.server 8790 --bind 127.0.0.1
timeout /t 3 /nobreak >nul
start "" http://127.0.0.1:8790/index.html
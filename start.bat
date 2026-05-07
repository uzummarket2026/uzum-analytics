@echo off
chcp 65001 > nul
echo ========================================================
echo Uzum Analytics - ishga tushirish (Dockersiz)
echo ========================================================
echo.

REM --- Backend (Python uvicorn, system Python) ---
echo [1/2] Backend (FastAPI) ishga tushirilmoqda... port 8000
start "Uzum Backend" cmd /k "cd /d %~dp0backend && python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"

REM --- Frontend (Next.js) ---
echo [2/2] Frontend (Next.js) ishga tushirilmoqda... port 3000
start "Uzum Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Tayyor! Ikkita yangi oyna ochildi.
echo   Backend:  http://127.0.0.1:8000
echo   Frontend: http://localhost:3000
echo.
echo Eslatma: birinchi marta ishga tushirsangiz, frontend uchun
echo   cd frontend ^&^& npm install
echo bajarilgan bo'lishi kerak.
echo.
pause

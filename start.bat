@echo off
echo ========================================================
echo Uzum Analytics Loyihasini Ishga Tushirish
echo ========================================================

echo Backend serveri ishga tushirilmoqda...
cd backend
start cmd /k ".\venv\Scripts\activate && uvicorn app.main:app --reload"

echo Frontend serveri ishga tushirilmoqda...
cd ../frontend
start cmd /k "npm run dev"

echo.
echo Loyiha muvaffaqiyatli ishga tushirildi!
echo Ikkita yangi oyna ochildi (biri Backend uchun, biri Frontend uchun).
echo Asosiy sahifa: http://localhost:3000
echo.
pause

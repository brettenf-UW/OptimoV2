@echo off
echo.
echo OptimoV2 Frontend Tester
echo ========================
echo.
echo Starting servers...
echo.

cd optimo-frontend

:: Start both servers
start "Mock API Server" cmd /k "npm run mock-server"
timeout /t 2 /nobreak > nul
start "React Frontend" cmd /k "npm start"

echo.
echo Servers starting! Browser will open in 30-60 seconds...
echo.
echo TEST WITH THESE FILES:
echo   C:\dev\OptimoV2\data\base\
echo.
echo To stop: Close both command windows
echo.
pause
@echo off
echo =========================================
echo OptimoV2 Frontend Deployment to GitHub Pages
echo =========================================
echo.

REM Check if we're in the right directory
if not exist "optimo-frontend\package.json" (
    echo ERROR: Please run this script from the OptimoV2 root directory
    pause
    exit /b 1
)

REM Check if git is initialized
git status >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not initialized in this directory
    echo Please initialize git and set up your GitHub repository first
    echo See FRONTEND_DEPLOYMENT_GUIDE.md for instructions
    pause
    exit /b 1
)

REM Get current git remote
for /f "tokens=2" %%i in ('git remote -v ^| findstr "origin.*fetch"') do set REMOTE_URL=%%i

if "%REMOTE_URL%"=="" (
    echo ERROR: No git remote 'origin' found
    echo Please add your GitHub repository as origin:
    echo git remote add origin https://github.com/YOUR_USERNAME/OptimoV2.git
    pause
    exit /b 1
)

echo Git remote found: %REMOTE_URL%
echo.

REM Extract username from remote URL
for /f "tokens=4 delims=/" %%i in ("%REMOTE_URL%") do set GITHUB_USER=%%i

echo Detected GitHub username: %GITHUB_USER%
echo.

REM Ask for confirmation
set /p CONFIRM=Is this correct? (Y/N): 
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo Please update the homepage in optimo-frontend\package.json manually
    echo Then run: cd optimo-frontend ^&^& npm run deploy
    pause
    exit /b 1
)

echo.
echo Updating package.json with your GitHub username...

REM Update package.json (using PowerShell for JSON manipulation)
powershell -Command "(Get-Content 'optimo-frontend\package.json' -Raw) -replace '\"homepage\": \"https://.*\.github\.io/OptimoV2\"', '\"homepage\": \"https://%GITHUB_USER%.github.io/OptimoV2\"' | Set-Content 'optimo-frontend\package.json'"

echo.
echo Building and deploying frontend...
echo.

cd optimo-frontend

REM Build the project
echo Building production version...
call npm run build

if errorlevel 1 (
    echo.
    echo ERROR: Build failed
    cd ..
    pause
    exit /b 1
)

echo.
echo Deploying to GitHub Pages...
call npm run deploy

if errorlevel 1 (
    echo.
    echo ERROR: Deployment failed
    cd ..
    pause
    exit /b 1
)

cd ..

echo.
echo =========================================
echo Deployment Complete!
echo =========================================
echo.
echo Your site will be available at:
echo https://%GITHUB_USER%.github.io/OptimoV2
echo.
echo Note: It may take 5-10 minutes for the site to become available
echo.
echo REMEMBER: The deployed site shows mock data only (not real optimization results)
echo.
pause
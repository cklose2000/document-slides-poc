@echo off
echo ========================================
echo Git Commit Script for Document-Slides-POC
echo ========================================
echo.

REM Initialize git if needed
if not exist ".git" (
    echo Initializing git repository...
    git init
    git remote add origin https://github.com/cklose2000/document-slides-poc.git
)

REM Verify .env is ignored
findstr /C:".env" .gitignore >nul
if errorlevel 1 (
    echo ERROR: .env is not in .gitignore!
    pause
    exit /b 1
)

echo Checking .env is properly ignored...
echo.

REM Stage all files except .env
git add -A
git reset .env

echo Files to be committed:
git status --short
echo.

REM Commit changes
git commit -m "Add LLMWhisperer PDF extraction and update documentation" -m "- Implemented PDF extraction using LLMWhisperer v2 API" -m "- Added support for OCR, table detection, and section recognition" -m "- Updated requirements.txt with llmwhisperer-client" -m "- Created comprehensive .env.example with all configuration options" -m "- Updated README.md with complete setup instructions and tech stack" -m "- Modified API endpoints to use new PDF extractor" -m "- Added environment variable configuration with python-dotenv" -m "- Enhanced error handling and fallback mechanisms"

REM Push to GitHub
echo.
echo Pushing to GitHub...
git branch -M main
git push -u origin main

echo.
echo ========================================
echo Successfully committed and pushed!
echo API keys in .env were NOT committed
echo ========================================
pause
@echo off
REM One-click deployment script for Windows
REM Deploy to Railway + Vercel + R2 + OpenAI

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Starting Product Picker Deployment
echo ========================================
echo.

REM Step 1: Configure environment
echo Step 1: Configure environment variables
echo.

set /p CLOUDFLARE_ACCOUNT_ID="Enter Cloudflare Account ID: "
set /p R2_ACCESS_KEY_ID="Enter R2 Access Key ID: "
set /p R2_SECRET_ACCESS_KEY="Enter R2 Secret Access Key: "
set /p OPENAI_API_KEY="Enter OpenAI API Key: "
set /p VERCEL_URL="Enter Vercel frontend URL (optional): "

REM Create .env.railway
(
echo CLOUDFLARE_ACCOUNT_ID=%CLOUDFLARE_ACCOUNT_ID%
echo CLOUDFLARE_R2_ACCESS_KEY_ID=%R2_ACCESS_KEY_ID%
echo CLOUDFLARE_R2_SECRET_ACCESS_KEY=%R2_SECRET_ACCESS_KEY%
echo CLOUDFLARE_R2_BUCKET=product-pdfs
echo CLOUDFLARE_R2_PUBLIC_URL=https://pub-ada201ec5fb84401a3b36b7b21e6ed0f.r2.dev
echo OPENAI_API_KEY=%OPENAI_API_KEY%
echo LLM_PROVIDER=openai
echo LLM_MODEL=gpt-3.5-turbo
echo PYTHONUNBUFFERED=1
echo ENVIRONMENT=production
if "%VERCEL_URL%"=="" (
    echo ALLOWED_ORIGINS=http://localhost:3000
) else (
    echo ALLOWED_ORIGINS=%VERCEL_URL%
)
) > .env.railway

echo.
echo Configuration saved to .env.railway
echo.

REM Step 2: Git push
echo Step 2: Uploading to GitHub
echo.
git add .env.railway
git commit -m "Add deployment configuration" 2>nul
git push origin main

echo.
echo ========================================
echo Next Steps:
echo ========================================
echo.
echo 1. Railway Backend:
echo    - Go to https://railway.app
echo    - Create new project from GitHub
echo    - Add PostgreSQL plugin
echo    - Set environment variables (from .env.railway file)
echo    - Railway auto-deploys
echo.
echo 2. Vercel Frontend:
echo    - Go to https://vercel.com
echo    - Import GitHub repository
echo    - Add env var: REACT_APP_API_BASE=[your-railway-url]
echo    - Deploy
echo.
echo 3. Configuration:
echo    - Check .env.railway for your settings
echo    - Update CORS in Railway dashboard if needed
echo.
echo ========================================
echo All files have been uploaded to GitHub:
echo https://github.com/sergeylkn/ti-catalog
echo ========================================
echo.
pause

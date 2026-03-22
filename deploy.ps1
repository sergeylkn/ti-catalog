# One-click deployment script for Windows
# Deploy to Railway + Vercel + R2 + OpenAI

Write-Host "🚀 Starting Product Picker deployment..." -ForegroundColor Green
Write-Host ""

# Check prerequisites
Write-Host "📋 Checking prerequisites..." -ForegroundColor Yellow

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git not installed" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Git installed" -ForegroundColor Green

# Step 1: Configure environment
Write-Host ""
Write-Host "⚙️  Step 1: Configure environment variables" -ForegroundColor Yellow
Write-Host ""

$CLOUDFLARE_ACCOUNT_ID = Read-Host "Enter Cloudflare Account ID"
$R2_ACCESS_KEY_ID = Read-Host "Enter R2 Access Key ID"
$R2_SECRET_ACCESS_KEY = Read-Host "Enter R2 Secret Access Key" -AsSecureString
$R2_SECRET_ACCESS_KEY_TEXT = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($R2_SECRET_ACCESS_KEY))
$OPENAI_API_KEY = Read-Host "Enter OpenAI API Key" -AsSecureString
$OPENAI_API_KEY_TEXT = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($OPENAI_API_KEY))
$VERCEL_URL = Read-Host "Enter Vercel frontend URL (or press Enter to skip)"

# Create .env.railway
$env_content = @"
CLOUDFLARE_ACCOUNT_ID=$CLOUDFLARE_ACCOUNT_ID
CLOUDFLARE_R2_ACCESS_KEY_ID=$R2_ACCESS_KEY_ID
CLOUDFLARE_R2_SECRET_ACCESS_KEY=$R2_SECRET_ACCESS_KEY_TEXT
CLOUDFLARE_R2_BUCKET=product-pdfs
CLOUDFLARE_R2_PUBLIC_URL=https://pub-ada201ec5fb84401a3b36b7b21e6ed0f.r2.dev
OPENAI_API_KEY=$OPENAI_API_KEY_TEXT
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
PYTHONUNBUFFERED=1
ENVIRONMENT=production
ALLOWED_ORIGINS=$($VERCEL_URL -eq "" ? "http://localhost:3000" : $VERCEL_URL)
"@

$env_content | Out-File -FilePath .env.railway -Encoding UTF8
Write-Host "✅ Configuration saved to .env.railway" -ForegroundColor Green

# Step 2: Instructions for Railway
Write-Host ""
Write-Host "📦 Step 2: Deploy to Railway" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Go to https://railway.app" -ForegroundColor Cyan
Write-Host "2. Sign in with GitHub" -ForegroundColor Cyan
Write-Host "3. Create new project" -ForegroundColor Cyan
Write-Host "4. Add PostgreSQL plugin" -ForegroundColor Cyan
Write-Host "5. Connect your GitHub repository" -ForegroundColor Cyan
Write-Host "6. Set environment variables from .env.railway file:" -ForegroundColor Cyan
Write-Host ""
Get-Content .env.railway | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
Write-Host ""
Write-Host "7. Railway will auto-detect Procfile and deploy" -ForegroundColor Cyan
Write-Host ""
$continue = Read-Host "Press Enter when Railway deployment is complete..."

# Step 3: Get Railway URL
Write-Host ""
Write-Host "🔗 Railway URL" -ForegroundColor Yellow
$RAILWAY_URL = Read-Host "Enter your Railway app URL (e.g., https://app.up.railway.app)"

# Step 4: Instructions for Vercel
Write-Host ""
Write-Host "📦 Step 3: Deploy to Vercel" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Go to https://vercel.com" -ForegroundColor Cyan
Write-Host "2. Click 'Add New' -> 'Project'" -ForegroundColor Cyan
Write-Host "3. Import your GitHub repository" -ForegroundColor Cyan
Write-Host "4. Vercel will auto-detect frontend/ folder" -ForegroundColor Cyan
Write-Host "5. Add environment variable:" -ForegroundColor Cyan
Write-Host "   REACT_APP_API_BASE=$RAILWAY_URL" -ForegroundColor Cyan
Write-Host "6. Click Deploy" -ForegroundColor Cyan
Write-Host ""
$continue = Read-Host "Press Enter when Vercel deployment is complete..."

# Step 5: Verification
Write-Host ""
Write-Host "✅ Verifying deployment..." -ForegroundColor Yellow
Write-Host ""

$VERCEL_DOMAIN = Read-Host "Enter your Vercel domain (e.g., app.vercel.app)"

# Test backend
Write-Host "Testing backend health..." -ForegroundColor Cyan
try {
    $health = Invoke-WebRequest -Uri "$RAILWAY_URL/health" -UseBasicParsing -TimeoutSec 5
    if ($health.StatusCode -eq 200) {
        Write-Host "✅ Backend is responding" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Backend not responding yet (may need a moment to start)" -ForegroundColor Yellow
}

# Summary
Write-Host ""
Write-Host "═══════════════════════════════════════" -ForegroundColor Green
Write-Host "🎉 DEPLOYMENT COMPLETE!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 URLs:" -ForegroundColor Cyan
Write-Host "   Backend:  $RAILWAY_URL" -ForegroundColor White
Write-Host "   Frontend: https://$VERCEL_DOMAIN" -ForegroundColor White
Write-Host ""
Write-Host "📊 API Endpoints:" -ForegroundColor Cyan
Write-Host "   Health:   GET  $RAILWAY_URL/health" -ForegroundColor White
Write-Host "   Search:   POST $RAILWAY_URL/search" -ForegroundColor White
Write-Host "   Chat:     POST $RAILWAY_URL/chat" -ForegroundColor White
Write-Host "   Docs:     $RAILWAY_URL/docs" -ForegroundColor White
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor Cyan
Write-Host "   1. Test the frontend at https://$VERCEL_DOMAIN" -ForegroundColor White
Write-Host "   2. Try searching for products" -ForegroundColor White
Write-Host "   3. Ask questions using RAG chat" -ForegroundColor White
Write-Host "   4. Monitor logs in Railway/Vercel dashboards" -ForegroundColor White
Write-Host ""
Write-Host "✨ Happy cataloging! ✨" -ForegroundColor Green

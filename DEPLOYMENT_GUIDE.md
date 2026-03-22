# Railway Deployment Guide

## 1️⃣ Backend Setup (Railway)

### Step 1: Create Railway Account
- Go to https://railway.app
- Sign up with GitHub

### Step 2: Create PostgreSQL Database
1. In Railway dashboard, click "Create Project"
2. Select "PostgreSQL"
3. Copy `DATABASE_URL` to clipboard

### Step 3: Deploy Backend
1. Connect your GitHub repository to Railway
2. Create new project from repo
3. In Railway dashboard, add environment variables:

```
DATABASE_URL=<from PostgreSQL>
CLOUDFLARE_ACCOUNT_ID=your_account_id
CLOUDFLARE_R2_ACCESS_KEY_ID=your_key
CLOUDFLARE_R2_SECRET_ACCESS_KEY=your_secret
CLOUDFLARE_R2_BUCKET=product-pdfs
CLOUDFLARE_R2_PUBLIC_URL=https://pub-ada201ec5fb84401a3b36b7b21e6ed0f.r2.dev
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
PYTHONUNBUFFERED=1
ENVIRONMENT=production
ALLOWED_ORIGINS=https://yourfrontend.vercel.app,http://localhost:3000
```

4. Railway will automatically detect `railway.json` and deploy
5. After deployment, run initialization:
   ```bash
   railway run python scripts/download_pdfs_from_r2.py
   railway run python scripts/generate_embeddings.py
   ```

6. Copy the Railway URL: `https://your-app.up.railway.app`

---

## 2️⃣ Frontend Setup (Vercel)

### Step 1: Prepare Frontend
1. Update `frontend/package.json` - build command is already set
2. Make sure `frontend/vercel.json` exists

### Step 2: Deploy to Vercel
1. Go to https://vercel.com
2. Sign up with GitHub
3. Click "Import Project"
4. Select your GitHub repository
5. Vercel will auto-detect `frontend/` as root
6. Add environment variable:
   ```
   REACT_APP_API_BASE=https://your-railway-app.up.railway.app
   ```
7. Click Deploy

Your frontend URL: `https://your-project.vercel.app`

---

## 3️⃣ Cloudflare R2 Setup

### Get R2 Credentials
1. Go to Cloudflare Dashboard
2. Navigate to "R2" → "API Tokens"
3. Create new API token with S3 permissions:
   - Account ID: `your_account_id`
   - Access Key ID: `CLOUDFLARE_R2_ACCESS_KEY_ID`
   - Secret Access Key: `CLOUDFLARE_R2_SECRET_ACCESS_KEY`
4. Your bucket: `product-pdfs`
5. Public URL: `https://pub-ada201ec5fb84401a3b36b7b21e6ed0f.r2.dev`

---

## 4️⃣ OpenAI API Setup

1. Go to https://openai.com/api/keys
2. Create new API key
3. Copy: `sk-...` format
4. Use as `OPENAI_API_KEY` environment variable

---

## 📋 Architecture Overview

```
┌─────────────────────────────────────────┐
│ Vercel Frontend (React + Material-UI)  │
│ https://yourapp.vercel.app             │
└────────────────┬────────────────────────┘
                 │ REST API (HTTPS)
                 ▼
┌─────────────────────────────────────────┐
│ Railway Backend (FastAPI + PostgreSQL) │
│ https://your-app.up.railway.app        │
│ ├─ /search          → Full-text search│
│ ├─ /filter          → Advanced filters │
│ ├─ /chat            → RAG with OpenAI │
│ ├─ /recommendations → Similar products│
│ └─ /pdf/index-from-r2 → Background job│
└────────────────┬────────────────────────┘
                 │
        ┌────────┼────────┐
        ▼        ▼        ▼
    ┌────────┐ ┌──────┐ ┌─────────┐
    │ R2     │ │ PgSQL│ │ OpenAI  │
    │ Storage│ │ 256MB│ │ API     │
    └────────┘ └──────┘ └─────────┘
```

---

## 🚀 Deployment Checklist

### Pre-deployment
- [ ] GitHub repo with all code
- [ ] R2 bucket with PDFs and manifest
- [ ] OpenAI API key ready
- [ ] Cloudflare R2 credentials ready

### Railway Deployment
- [ ] PostgreSQL database created
- [ ] Backend environment variables set
- [ ] `railway.json` detected
- [ ] Backend deployed successfully
- [ ] `railway run` scripts executed for data init

### Vercel Deployment
- [ ] Frontend environment variable set
- [ ] GitHub integration connected
- [ ] Frontend deployed successfully
- [ ] API URL verified in browser console

### Post-deployment Testing
```bash
# Test backend health
curl https://your-app.up.railway.app/health

# Test search
curl -X POST https://your-app.up.railway.app/search \
  -H "Content-Type: application/json" \
  -d '{"query": "шланг"}'

# Test RAG chat
curl -X POST https://your-app.up.railway.app/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test", "message": "What hose for 16 bar?"}'
```

---

## 📊 Costs Estimate (Monthly)

| Service | Free Tier | Paid |
|---------|-----------|------|
| Railway | 5$ credits | $5-50/mo |
| Vercel | ✅ Free | $20/mo |
| R2 | 10GB free | $0.015/GB |
| OpenAI API | - | $0.002/1K tokens |
| **Total** | **~5$/mo** | **$25-80/mo** |

---

## 🔒 Security Notes

1. **Never commit secrets** - use environment variables only
2. **CORS configured** - only allow your Vercel domain
3. **PostgreSQL password** - Railway generates secure password
4. **R2 credentials** - use limited API tokens, rotate regularly
5. **OpenAI key** - use separate key for production, monitor usage

---

## 🛠️ Maintenance

### Monitor Performance
- Railway dashboard: CPU, memory, network
- Vercel dashboard: response times, error rate
- OpenAI dashboard: API usage, costs

### Scale if Needed
- Railway: increase database size, add caching
- Vercel: automatic scaling (no action needed)
- OpenAI: upgrade to GPT-4 for better responses

### Update PDFs
```bash
# On Railway, run manually:
railway run python scripts/download_pdfs_from_r2.py
railway run python scripts/generate_embeddings.py
```

---

## 📞 Troubleshooting

### Backend not responding
```bash
# Check Railway logs
railway logs

# Check database connection
railway run python -c "import os; print(os.getenv('DATABASE_URL'))"
```

### Frontend API errors
```javascript
// Check browser console
console.log(process.env.REACT_APP_API_BASE)
```

### Missing embeddings
```bash
# Regenerate on Railway
railway run python scripts/generate_embeddings.py
```

### R2 access denied
- Verify R2 credentials in Railway env vars
- Check bucket name matches
- Ensure API token has S3 permissions

---

## 🎯 Next Steps

1. Monitor performance in first week
2. Optimize queries if slow
3. Add monitoring/alerts (Sentry, DataDog)
4. Scale database if needed
5. Consider Redis for caching

✅ **Full production deployment ready!**

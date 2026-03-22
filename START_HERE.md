# 🌐 INTERACTIVE PRODUCT PICKER

## Cloud-Ready Product Discovery System

**Railway + Vercel + Cloudflare R2 + OpenAI**

---

## ⚡ START IN 5 MINUTES

### Option 1: Auto Deploy (Recommended)

```bash
chmod +x deploy.sh
./deploy.sh
```

Enter your credentials and we'll handle the rest:
- ✅ Backend deploys to Railway
- ✅ Frontend deploys to Vercel  
- ✅ R2 storage configured
- ✅ OpenAI integration active
- ✅ Production ready!

### Option 2: Docker

```bash
docker-compose up --build
```

Access:
- Frontend: http://localhost:3000
- Backend: http://localhost:8000/docs

---

## 📦 FEATURES

✅ Full-text search  
✅ Semantic search (embeddings)  
✅ RAG Q&A (OpenAI GPT)  
✅ Recommendations  
✅ Advanced filters  
✅ Material-UI UI  
✅ Production optimized  
✅ 500MB memory limit OK  

---

## 🏗️ ARCHITECTURE

```
Vercel (Frontend) ↔ Railway (Backend) ↔ PostgreSQL
                        ↓
              ┌────┬─────┴─────┬────┐
              R2    Embeddings  OpenAI
```

---

## 📚 DOCUMENTATION

| Document | Purpose |
|----------|---------|
| [QUICK_START_CLOUD.md](QUICK_START_CLOUD.md) | 5-minute setup |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Detailed instructions |
| [CLOUD_DEPLOYMENT_COMPLETE.md](CLOUD_DEPLOYMENT_COMPLETE.md) | Architecture & troubleshooting |
| [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) | Technical details |
| [DEPLOYMENT_COMPLETE.md](DEPLOYMENT_COMPLETE.md) | What's included |

---

## 🔑 REQUIREMENTS

1. **Cloudflare R2** — API credentials
2. **OpenAI** — API key (sk-...)
3. **GitHub** — Repository for auto-deploy

---

## 📊 PERFORMANCE

| Operation | Time |
|-----------|------|
| Search | <100ms |
| Filter | <200ms |
| RAG Chat | 2-5s |
| Page Load | <2s |

---

## 💰 COST

| Service | Cost |
|---------|------|
| Railway | $5-50/mo |
| Vercel | Free |
| R2 | $0.015/GB |
| OpenAI | ~$1-5/1K reqs |
| **Total** | **$5-25/mo** |

---

## ✅ READY TO DEPLOY!

Everything is production-ready. Choose your path:

### 🚀 Fast Path (Auto)
```bash
./deploy.sh
```

### 📖 Manual Path (Full Control)
1. Create Railway project
2. Create Vercel project
3. Set environment variables
4. Deploy!

### 🐳 Local Development
```bash
docker-compose up --build
```

---

## 🎯 WHAT'S INCLUDED

✅ FastAPI backend (production-optimized)  
✅ React frontend (TypeScript)  
✅ PostgreSQL (256MB)  
✅ PDF parser  
✅ Embeddings (384 dims)  
✅ RAG engine (OpenAI)  
✅ R2 integration  
✅ Deployment scripts  
✅ Full documentation  

---

## 🚀 GET STARTED

```bash
# Clone repository
git clone <your-repo>
cd product-picker

# Deploy to cloud
chmod +x deploy.sh
./deploy.sh

# Follow prompts and you're done!
```

Or read [QUICK_START_CLOUD.md](QUICK_START_CLOUD.md) for detailed steps.

---

**Made for industrial product discovery 🛠️**

Questions? Check the documentation files above ⬆️

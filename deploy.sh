#!/bin/bash
# One-click deployment script
# Run this after setting up Railway, Vercel, R2, OpenAI accounts

set -e

echo "🚀 Starting deployment..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command -v git &> /dev/null; then
    echo -e "${RED}❌ Git not installed${NC}"
    exit 1
fi

if ! command -v railway &> /dev/null; then
    echo -e "${YELLOW}⚠️  Railway CLI not installed${NC}"
    echo "   Install from: https://docs.railway.app/guides/cli"
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Step 1: Configure environment
echo -e "${YELLOW}⚙️  Step 1: Configure environment variables${NC}"

read -p "Enter Cloudflare Account ID: " CLOUDFLARE_ACCOUNT_ID
read -p "Enter R2 Access Key ID: " R2_ACCESS_KEY_ID
read -sp "Enter R2 Secret Access Key: " R2_SECRET_ACCESS_KEY
echo
read -sp "Enter OpenAI API Key: " OPENAI_API_KEY
echo
read -p "Enter Vercel frontend URL (leave blank to skip): " VERCEL_URL

# Create .env files
cat > .env.railway << EOF
CLOUDFLARE_ACCOUNT_ID=$CLOUDFLARE_ACCOUNT_ID
CLOUDFLARE_R2_ACCESS_KEY_ID=$R2_ACCESS_KEY_ID
CLOUDFLARE_R2_SECRET_ACCESS_KEY=$R2_SECRET_ACCESS_KEY
CLOUDFLARE_R2_BUCKET=product-pdfs
CLOUDFLARE_R2_PUBLIC_URL=https://pub-ada201ec5fb84401a3b36b7b21e6ed0f.r2.dev
OPENAI_API_KEY=$OPENAI_API_KEY
LLM_PROVIDER=openai
LLM_MODEL=gpt-3.5-turbo
PYTHONUNBUFFERED=1
ENVIRONMENT=production
ALLOWED_ORIGINS=${VERCEL_URL:-"http://localhost:3000"}
EOF

echo -e "${GREEN}✅ Configuration saved to .env.railway${NC}"

# Step 2: Deploy to Railway
echo -e "${YELLOW}📦 Step 2: Deploying to Railway...${NC}"

if command -v railway &> /dev/null; then
    railway login --force
    railway link

    # Create PostgreSQL plugin if needed
    railway add --service postgres

    # Deploy
    railway up

    # Get Railway URL
    RAILWAY_URL=$(railway domain)
    echo -e "${GREEN}✅ Railway deployment complete!${NC}"
    echo "   URL: $RAILWAY_URL"

    # Run initialization
    echo -e "${YELLOW}🔄 Initializing database...${NC}"
    railway run python scripts/download_pdfs_from_r2.py
    railway run python scripts/generate_embeddings.py
else
    echo -e "${YELLOW}⚠️  Railway CLI not found. Manual deployment required.${NC}"
    echo "   1. Go to https://railway.app"
    echo "   2. Create new project from GitHub"
    echo "   3. Add PostgreSQL plugin"
    echo "   4. Set environment variables from .env.railway"
    echo "   5. Deploy"
    read -p "   Press Enter when deployment is complete..."
fi

# Step 3: Deploy to Vercel
echo -e "${YELLOW}📦 Step 3: Deploying to Vercel...${NC}"

cat > frontend/vercel.json << EOF
{
  "buildCommand": "npm install && npm run build",
  "outputDirectory": "build",
  "env": {
    "REACT_APP_API_BASE": "${RAILWAY_URL:-"https://your-app.up.railway.app"}"
  }
}
EOF

read -p "Deploy to Vercel manually via https://vercel.com? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Steps:${NC}"
    echo "1. Go to https://vercel.com"
    echo "2. Click 'Import Project'"
    echo "3. Select your GitHub repository"
    echo "4. Vercel will auto-detect frontend/ folder"
    echo "5. Add environment variable:"
    echo "   REACT_APP_API_BASE=${RAILWAY_URL:-"https://your-app.up.railway.app"}"
    echo "6. Click 'Deploy'"
    read -p "Press Enter when deployment is complete..."
fi

# Step 4: Verify deployment
echo -e "${YELLOW}✅ Verifying deployment...${NC}"

BACKEND_URL="${RAILWAY_URL:-https://your-app.up.railway.app}"

# Test backend
echo "Testing backend health..."
if curl -s "$BACKEND_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ Backend is responding${NC}"
else
    echo -e "${YELLOW}⚠️  Backend not responding yet (may need a moment to start)${NC}"
fi

# Test database
echo "Testing database..."
if railway run python -c "from backend.models import init_db; init_db()" 2>/dev/null; then
    echo -e "${GREEN}✅ Database initialized${NC}"
else
    echo -e "${YELLOW}⚠️  Database check failed${NC}"
fi

# Summary
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo
echo "🔗 URLs:"
echo "   Backend:  $BACKEND_URL"
echo "   Frontend: ${VERCEL_URL:-"https://your-project.vercel.app"}"
echo
echo "📊 API Endpoints:"
echo "   Health:   GET  $BACKEND_URL/health"
echo "   Search:   POST $BACKEND_URL/search"
echo "   Chat:     POST $BACKEND_URL/chat"
echo "   Docs:     $BACKEND_URL/docs"
echo
echo "🛠️  Management:"
echo "   Railway logs:   railway logs"
echo "   Railway shell:  railway shell"
echo "   Run commands:   railway run <command>"
echo
echo "📝 Next steps:"
echo "   1. Test the frontend at $VERCEL_URL"
echo "   2. Try searching for products"
echo "   3. Ask questions using RAG chat"
echo "   4. Monitor logs in Railway/Vercel dashboards"
echo
echo -e "${GREEN}✨ Happy cataloging! ✨${NC}"

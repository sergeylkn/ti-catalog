#!/bin/bash
# Quick setup for Railway + Vercel deployment
# This is the official way to deploy to Railway

# Create Procfile for Railway
cat > Procfile << EOF
web: gunicorn -w 4 -b 0.0.0.0:\$PORT backend.app:app
worker: python scripts/download_pdfs_from_r2.py && python scripts/generate_embeddings.py
EOF

# Create runtime.txt for Python version
cat > runtime.txt << EOF
python-3.11.6
EOF

echo "✅ Railway configuration created"
echo ""
echo "🚀 To deploy to Railway:"
echo ""
echo "1. Install Railway CLI:"
echo "   npm i -g @railway/cli"
echo ""
echo "2. Connect your GitHub repo to Railway (via dashboard)"
echo ""
echo "3. Set environment variables in Railway dashboard:"
cat .env.railway
echo ""
echo "4. Railway will auto-detect Procfile and deploy"
echo ""
echo "5. After deployment, run initialization:"
echo "   railway run python scripts/download_pdfs_from_r2.py"
echo "   railway run python scripts/generate_embeddings.py"

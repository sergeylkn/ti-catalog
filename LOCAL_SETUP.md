# Install dependencies and run the stack locally (without Docker)

## Prerequisites
- Python 3.9+
- Node.js 18+ and npm
- Git

## Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the server
python app.py
# or
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at **http://localhost:8000**
- API Docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend will open automatically at **http://localhost:3000**

## Running Both Services

### Option 1: Two Terminal Windows
Terminal 1 (Backend):
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python app.py
```

Terminal 2 (Frontend):
```bash
cd frontend
npm start
```

### Option 2: Using a Process Manager (Concurrently)

```bash
# Install concurrently globally (optional)
npm install -g concurrently

# From root directory
npm install concurrently

# Add to root package.json:
# "scripts": {
#   "dev": "concurrently \"cd backend && python app.py\" \"cd frontend && npm start\""
# }

npm run dev
```

## Environment Variables

Create `.env` file in root:
```
REACT_APP_API_BASE=http://localhost:8000
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
DEBUG=True
```

## Testing the API

```bash
# Health check
curl http://localhost:8000/health

# Get categories
curl http://localhost:8000/categories

# Search products
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "шланг", "limit": 10}'

# Get stats
curl http://localhost:8000/stats
```

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (should be 3.9+)
- Check port 8000 is not in use: `netstat -an | grep 8000`
- Try a different port: `uvicorn app:app --port 8001`

### Frontend won't start
- Delete `node_modules` and `package-lock.json`, then `npm install`
- Clear npm cache: `npm cache clean --force`
- Try a different port: `PORT=3001 npm start`

### CORS errors
- Make sure backend is running and accessible
- Check `REACT_APP_API_BASE` is set correctly

## Next Steps

1. Run `python scripts/analyze_and_generate_parsers.py` to download and analyze PDFs
2. Implement PDF parsing logic in `parsers/` directory
3. Set up vector DB (Qdrant/Pinecone) for better recommendations
4. Add database (PostgreSQL) for persistent storage

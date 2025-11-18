#!/bin/bash
# Substrate API Server Startup Script

echo "================================="
echo "  Starting Substrate API Server  "
echo "================================="
echo ""

# Set Python path
export PYTHONPATH=/home/user/GerdsenAI-Frontier:$PYTHONPATH

# Check if dependencies are installed
echo "Checking dependencies..."
python -c "import fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing API dependencies..."
    pip install fastapi uvicorn pydantic python-multipart --quiet
fi

python -c "import sentence_transformers, chromadb" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing ML dependencies (this may take a few minutes)..."
    pip install sentence-transformers chromadb --quiet
fi

echo "✓ Dependencies ready"
echo ""

# Create data directory
mkdir -p ./substrate_data/chroma
echo "✓ Data directory ready"
echo ""

# Start the server
echo "Starting API server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

cd /home/user/GerdsenAI-Frontier
python -m uvicorn substrate.web.backend.api:app --host 0.0.0.0 --port 8000 --reload

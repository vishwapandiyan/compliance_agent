#!/bin/bash

# DevGuard Startup Script for EC2
# This script starts the Streamlit application

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting DevGuard Application...${NC}"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}📋 Loading environment variables from .env...${NC}"
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${RED}❌ Error: GEMINI_API_KEY environment variable is not set${NC}"
    echo -e "${YELLOW}   Please set it in .env file or export it as an environment variable${NC}"
    exit 1
fi

# Get port from environment or use default
PORT=${STREAMLIT_SERVER_PORT:-8501}
ADDRESS=${STREAMLIT_SERVER_ADDRESS:-0.0.0.0}

# Check if port is already in use
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${YELLOW}⚠️  Port $PORT is already in use${NC}"
    echo -e "${YELLOW}   Trying to kill existing process...${NC}"
    lsof -ti:$PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Start Streamlit
echo -e "${GREEN}🌐 Starting Streamlit on http://$ADDRESS:$PORT${NC}"
streamlit run app.py \
    --server.port=$PORT \
    --server.address=$ADDRESS \
    --server.headless=true \
    --browser.gatherUsageStats=false


#!/bin/bash

# DevGuard Deployment Script for EC2
# This script sets up the environment and deploys the application

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   DevGuard EC2 Deployment Script      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════╝${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Step 1: Update system packages
echo -e "${GREEN}[1/8] Updating system packages...${NC}"
sudo apt-get update -qq

# Step 2: Install Python and pip if not present
echo -e "${GREEN}[2/8] Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}   Installing Python 3...${NC}"
    sudo apt-get install -y python3 python3-pip python3-venv
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}   ✓ $PYTHON_VERSION installed${NC}"

# Step 3: Install system dependencies
echo -e "${GREEN}[3/8] Installing system dependencies...${NC}"
sudo apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    git \
    curl

# Step 4: Create virtual environment
echo -e "${GREEN}[4/8] Setting up Python virtual environment...${NC}"
if [ -d "venv" ]; then
    echo -e "${YELLOW}   Virtual environment already exists, recreating...${NC}"
    rm -rf venv
fi

python3 -m venv venv
source venv/bin/activate

# Step 5: Upgrade pip
echo -e "${GREEN}[5/8] Upgrading pip...${NC}"
pip install --upgrade pip setuptools wheel

# Step 6: Install Python dependencies
echo -e "${GREEN}[6/8] Installing Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}   ✓ Dependencies installed${NC}"
else
    echo -e "${RED}   ❌ requirements.txt not found${NC}"
    exit 1
fi

# Step 7: Set up environment variables
echo -e "${GREEN}[7/8] Setting up environment variables...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}   Creating .env from .env.example...${NC}"
        cp .env.example .env
        echo -e "${GREEN}   ℹ️  NVIDIA_API_KEY is optional - can be provided via frontend UI instead${NC}"
    else
        echo -e "${YELLOW}   Creating .env file...${NC}"
        cat > .env << EOF
# NVIDIA API Key (Optional - can be provided via frontend UI instead)
# NVIDIA_API_KEY=your_key_here  # Uncomment if you want to pre-fill UI
# NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1  # Default, usually don't need to change
# NVIDIA_MODEL=meta/llama-3.2-3b-instruct  # Default model

# AWS Configuration (Optional)
AWS_REGION=us-east-1
DEVGUARD_S3_BUCKET=
DEVGUARD_DYNAMODB_TABLE=

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
EOF
        echo -e "${GREEN}   ℹ️  NVIDIA_API_KEY is optional - users can enter it via the web UI${NC}"
    fi
else
    echo -e "${GREEN}   ✓ .env file already exists${NC}"
fi

# Step 8: Create reports directory
echo -e "${GREEN}[8/8] Creating reports directory...${NC}"
mkdir -p reports
touch reports/.gitkeep

# Make scripts executable
chmod +x start.sh

echo ""
echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Deployment Complete!                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}📋 Next Steps:${NC}"
echo -e "   1. Configure AWS credentials (if using S3/DynamoDB):"
echo -e "      aws configure"
    echo -e "   2. Edit .env file (optional - to pre-fill NVIDIA API key):"
    echo -e "      nano .env"
    echo -e "      # NVIDIA_API_KEY is optional - users can enter it via web UI"
    echo -e "   3. Start the application:"
    echo -e "      ./start.sh"
    echo -e "   4. Access the app and enter NVIDIA API key in the web UI"
echo ""
echo -e "${YELLOW}   Or use systemd service:${NC}"
echo -e "      sudo systemctl start devguard"
echo ""


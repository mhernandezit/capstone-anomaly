#!/bin/bash

echo "🔧 BGP Failure Detection Project Setup"
echo "======================================="

# Check Python version
echo "✅ Checking Python..."
if [[ -f "venv/bin/activate" ]]; then
    echo "   Virtual environment already exists"
    source venv/bin/activate
    echo "   Using Python $(python --version)"
else
    echo "   Creating virtual environment with Python 3.13..."
    /usr/local/opt/python@3.13/bin/python3 -m venv venv
    source venv/bin/activate
    echo "   Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Check Go
echo "✅ Checking Go..."
if command -v go &> /dev/null; then
    echo "   Go $(go version | cut -d' ' -f3) installed"
    echo "   Installing Go dependencies..."
    go mod tidy
else
    echo "   ❌ Go not found. Run: brew install go"
    exit 1
fi

# Check Docker
echo "✅ Checking Docker..."
if command -v docker &> /dev/null; then
    if docker info &> /dev/null; then
        echo "   Docker is running"
    else
        echo "   ⚠️  Docker installed but not running"
        echo "   Please start Docker Desktop from Applications"
    fi
else
    echo "   ❌ Docker not found. Run: brew install --cask docker"
    exit 1
fi

echo ""
echo "🚀 Setup complete! Next steps:"
echo "   1. Start Docker Desktop if not running"
echo "   2. Run 'make up' to start NATS + Dashboard"
echo "   3. Run 'make collector' to start the BGP collector"
echo "   4. Run 'make pipeline' to start the Python pipeline"
echo ""
echo "📊 Dashboard will be at: http://localhost:8501"
echo "📡 NATS will be at: nats://localhost:4222"

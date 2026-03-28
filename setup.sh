#!/bin/bash
# Quick Start Setup Script for LLM Training Data Generator
# This script sets up a development environment and demonstrates the pipeline

set -e

echo "================================================================"
echo "LLM Training Data Generator - Quick Start Setup"
echo "================================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1 || true
echo "✓ pip upgraded"

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create config from template
echo ""
echo "Setting up configuration..."
if [ ! -f "config.yaml" ]; then
    cp config.template.yaml config.yaml
    echo "✓ Created config.yaml from template"
    echo ""
    echo "⚠ NOTE: Edit config.yaml to add your data sources"
    echo "  - Add web sources with URLs"
    echo "  - Configure your LLM provider (OpenAI, Anthropic, or Ollama)"
    echo "  - Set API key environment variable if using API provider"
else
    echo "✓ config.yaml already exists"
fi

# Create directories
echo ""
echo "Creating output directories..."
mkdir -p datasets raw_content transformed_content
echo "✓ Directories created"

echo ""
echo "================================================================"
echo "Setup Complete!"
echo "================================================================"
echo ""
echo "Next steps:"
echo "1. Edit config.yaml with your data sources"
echo "2. Set API key if using cloud provider:"
echo "   export OPENAI_API_KEY=\"sk-...\""
echo "   export ANTHROPIC_API_KEY=\"sk-ant-...\""
echo "3. Run the pipeline:"
echo "   python main.py --config config.yaml"
echo ""
echo "For more information:"
echo "  - README.md: Overview and usage"
echo "  - CONFIG_GUIDE.md: Configuration documentation"
echo "  - ARCHITECTURE.md: System design"
echo ""

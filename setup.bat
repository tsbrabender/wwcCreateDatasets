@echo off
REM Quick Start Setup Script for LLM Training Data Generator (Windows)
REM This script sets up a development environment and demonstrates the pipeline

setlocal enabledelayedexpansion

echo.
echo ================================================================
echo LLM Training Data Generator - Quick Start Setup (Windows)
echo ================================================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.8+ from python.org
    pause
    exit /b 1
)
python --version
echo.

REM Create virtual environment
echo Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ^✓ Virtual environment created
) else (
    echo ^✓ Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo ^✓ Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel >nul 2>&1 || true
echo ^✓ pip upgraded
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo ^✓ Dependencies installed
echo.

REM Create config from template
echo Setting up configuration...
if not exist "config.yaml" (
    copy config.template.yaml config.yaml >nul
    echo ^✓ Created config.yaml from template
    echo.
    echo WARNING: Edit config.yaml to add your data sources
    echo   - Add web sources with URLs
    echo   - Configure your LLM provider (OpenAI, Anthropic, or Ollama)
    echo   - Set API key environment variable if using API provider
) else (
    echo ^✓ config.yaml already exists
)
echo.

REM Create directories
echo Creating output directories...
if not exist "datasets" mkdir datasets
if not exist "raw_content" mkdir raw_content
if not exist "transformed_content" mkdir transformed_content
echo ^✓ Directories created
echo.

echo ================================================================
echo Setup Complete!
echo ================================================================
echo.
echo Next steps:
echo 1. Edit config.yaml with your data sources
echo 2. Set API key if using cloud provider (in Command Prompt):
echo    set OPENAI_API_KEY=sk-...
echo    set ANTHROPIC_API_KEY=sk-ant-...
echo 3. Run the pipeline:
echo    python main.py --config config.yaml
echo.
echo For more information:
echo   - README.md: Overview and usage
echo   - CONFIG_GUIDE.md: Configuration documentation
echo   - ARCHITECTURE.md: System design
echo.
pause

# Getting Started Guide

Welcome to the LLM Training Data Generator! This guide will have you generating training datasets in minutes.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [First Run](#first-run)
4. [Understanding the Output](#understanding-the-output)
5. [Next Steps](#next-steps)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Python 3.8+** (check with `python --version`)
- **2 GB RAM** minimum (4+ GB for larger datasets)
- **Internet connection** (for web scraping and API calls)
- **Disk space**: ~100 MB for a small dataset

### Required for Cloud LLMs

- **OpenAI**: API key from https://platform.openai.com/api-keys
- **Anthropic**: API key from https://console.anthropic.com/

### Optional for Local LLM

- **Ollama**: Download from https://ollama.ai
- **Docker** (alternative to native Ollama)

## Installation

### Step 1: Clone or Download

```bash
git clone <repository-url> AutoTrain
cd AutoTrain
```

### Step 2: Run Setup Script

**On Linux/macOS:**
```bash
chmod +x setup.sh
./setup.sh
```

**On Windows:**
```bash
setup.bat
```

**Or Manual Setup:**
```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate.bat       # Windows CMD
venv\Scripts\Activate.ps1       # Windows PowerShell

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Verify Installation

```bash
# Test basic imports
python -c "import requests; print('✓ requests')"
python -c "import bs4; print('✓ beautifulsoup4')"
python -c "import yaml; print('✓ pyyaml')"
```

## First Run

### Quick Test with Demo Config

```bash
# Copy the template
cp config/config.template.yaml config/config.yaml

# Edit config/config.yaml and set a simple source
# For example, change to:
/*
sources:
  - name: "Python Docs Intro"
    url: "https://docs.python.org/3/tutorial/intro.html"
    scrape_type: "web"
    content_selector: "main"

llm:
  provider: "openai"
  model: "gpt-3.5-turbo"
  api_key: "${OPENAI_API_KEY}"
*/

# Set your API key
export OPENAI_API_KEY="sk-..."    # Linux/macOS
# or
set OPENAI_API_KEY=sk-...         # Windows CMD

# Run the pipeline
python main.py --config config/config.yaml --output ./my_dataset
```

### Or Use Ollama (Free, Local)

```bash
# Install and start Ollama
# Download from https://ollama.ai and install

# Start Ollama service
ollama serve

# In another terminal, pull a model
ollama pull mistral

# Update config/config.yaml to use Ollama:
/*
llm:
  provider: "ollama"
  model: "mistral"
  host: "http://localhost:11434"
*/

# Run the pipeline
python main.py --config config/config.yaml
```

### Monitor Progress

The pipeline outputs progress:

```
2024-01-15 10:30:00 - root - INFO - LLM Training Data Generator - Pipeline Start
2024-01-15 10:30:01 - root - INFO - WebScraper initialized with 2 workers
2024-01-15 10:30:02 - root - INFO - Step 1: Starting web scraping...
2024-01-15 10:30:05 - root - INFO - Successfully scraped: Python Docs
2024-01-15 10:30:06 - root - INFO - Step 2: Starting content transformation with LLM...
[... transformations ...]
2024-01-15 10:31:00 - root - INFO - Step 3: Generating datasets...
2024-01-15 10:31:05 - root - INFO - Step 4: Exporting datasets to JSONL...
2024-01-15 10:31:06 - root - INFO - Pipeline completed successfully!
```

## Understanding the Output

After running the pipeline, you'll find these files in your output directory:

### Directory Structure

```
datasets/
├── raw_content/                           # Original scraped content
│   └── python_docs_intro_web.json        # Raw HTML extracted
│
├── transformed/                           # LLM-transformed content
│   └── transformed_python_docs_intro_web.json
│
├── datasets/                              # Intermediate datasets
│   ├── instruction_response.jsonl
│   ├── summary.jsonl
│   ├── faq.jsonl
│   ├── guide.jsonl
│   ├── explanation.jsonl
│   └── multi_turn.jsonl
│
├── final_instruction_response.jsonl       # Validated JSONL
├── final_summary.jsonl
├── combined_training_data.jsonl           # All data combined
│
└── DATASET_SUMMARY.md                     # Statistics and info
```

### Key Files

**combined_training_data.jsonl** - Your main training file
- Contains all datasets combined
- Ready to use with UnSloth or Hugging Face
- One JSON object per line

**DATASET_SUMMARY.md** - Dataset report
- Item counts per type
- Category distribution
- Usage instructions
- JSONL schema reference

### Example JSONL Entry

```json
{
    "instruction": "What is Python?",
    "input": "",
    "output": "Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991.",
    "category": "instruction-response"
}
```

## Next Steps

### 1. Add More Data Sources

Edit `config/config.yaml` to add multiple sources:

```yaml
sources:
  - name: "Python Docs"
    url: "https://docs.python.org/3/"
    scrape_type: "web"
    content_selector: "main"
  
  - name: "FastAPI Guide"
    url: "https://fastapi.tiangolo.com"
    scrape_type: "web"
    content_selector: "article"
  
  - name: "Tutorial PDF"
    url: "https://example.com/guide.pdf"
    scrape_type: "pdf"
```

Then run:
```bash
python main.py --config config/config.yaml
```

### 2. Fine-tune a Model

Once you have your JSONL file, use it with UnSloth:

```python
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer

# Load your dataset
dataset = load_dataset('json', data_files='datasets/combined_training_data.jsonl')

# Fine-tune (example, see UnSloth docs for complete setup)
# model, tokenizer = FastLanguageModel.from_pretrained(...)
# trainer = SFTTrainer(...)
# trainer.train()
```

### 3. Explore Advanced Features

Use command-line options:
```bash
# Generate only FAQ dataset
python main.py --config config/config.yaml --dataset-type faq

# Use 4 concurrent workers for faster scraping
python main.py --config config/config.yaml --workers 4

# Enable debug logging
python main.py --config config/config.yaml --log-level DEBUG

# Skip scraping, only regenerate datasets from existing content
python main.py --config config/config.yaml --skip-scrape
```

### 4. Read Documentation

- **[README.md](README.md)** - Overview and features
- **[CONFIG_GUIDE.md](CONFIG_GUIDE.md)** - Configuration options
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design
- **[RATIONALE.md](RATIONALE.md)** - Design decisions

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'requests'"

**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "Invalid configuration: Cannot create output directory"

**Solution:** Check directory permissions
```bash
# Linux/macOS
chmod -R 755 ./datasets

# On Windows, right-click folder → Properties → Security
```

### Issue: Python version error

**Solution:** Check Python version and install if needed
```bash
python --version          # Should be 3.8+
python3 --version         # Try python3 if python fails

# On macOS, install with:
brew install python@3.11
```

### Issue: API Key errors

**Solution:** Set environment variable correctly
```bash
# Linux/macOS
export OPENAI_API_KEY="sk-..."

# Windows CMD
set OPENAI_API_KEY=sk-...

# Windows PowerShell
$env:OPENAI_API_KEY="sk-..."

# Verify it's set
echo $OPENAI_API_KEY        # Linux/macOS
echo %OPENAI_API_KEY%       # Windows
```

### Issue: "Failed to fetch URL"

**Causes:** 
- URL not accessible
- CSS selector incorrect  
- Rate limiting

**Solutions:**
```bash
# Test URL accessibility
curl https://your-url.com

# Use fewer workers to avoid rate limits
python main.py --config config/config.yaml --workers 1

# Find correct CSS selector by inspecting in browser (F12)
```

### Issue: "LLM connection failed"

**For OpenAI/Anthropic:**
- Verify API key is valid
- Check rate limits (may need to wait)
- Try with fewer items: `--batch-size 4`

**For Ollama:**
- Ensure Ollama is running: `ollama serve`
- Check correct host: default is `http://localhost:11434`

### Issue: Out of memory

**Solutions:**
```bash
# Reduce batch size
python main.py --config config/config.yaml --batch-size 8

# Use fewer workers
python main.py --config config/config.yaml --workers 1

# Process one dataset at a time
python main.py --config config/config.yaml --dataset-type summary
```

### Issue: Very slow performance

**Causes:** Too many workers, too large batch size

**Solutions:**
```bash
# Reduce workers (but not below 1)
python main.py --config config/config.yaml --workers 2

# Increase batch size (if you have memory)
python main.py --config config/config.yaml --batch-size 32

# Use local LLM (Ollama) instead of API
```

### Issue: "YAML parsing error"

**Solution:** Check YAML formatting
```bash
# Verify YAML syntax (requires Python)
python -c "import yaml; yaml.safe_load(open('config/config.yaml'))"

# Common issues:
# - Tabs instead of spaces (use 2 spaces)
# - Incorrect indentation
# - Missing colons after keys
```

## Getting Help

1. **Check logs** with `--log-level DEBUG`
   ```bash
   python main.py --config config/config.yaml --log-level DEBUG
   ```

2. **Verify configuration** matches schema in CONFIG_GUIDE.md

3. **Test components** individually:
   ```bash
   # Test web scraping
   python -c "from scraper import WebScraper; print('✓ scraper works')"
   ```

4. **Review documentation**:
   - CONFIG_GUIDE.md: Configuration issues
   - ARCHITECTURE.md: How components work
   - README.md: General usage

5. **Common issues**:
   - API key not set
   - URL not accessible
   - Incorrect CSS selector
   - Python version too old
   - Missing dependencies

## Quick Reference

### Command Examples

```bash
# Full pipeline, all dataset types
python main.py --config config/config.yaml

# Specific dataset type only
python main.py --config config/config.yaml --dataset-type instruction-response

# Skip scraping (reprocess existing content)
python main.py --config config/config.yaml --skip-scrape

# Use different output directory
python main.py --config config/config.yaml --output ./my_datasets

# More concurrent workers (faster scraping)
python main.py --config config/config.yaml --workers 4

# Debug mode with detailed logging
python main.py --config config/config.yaml --log-level DEBUG
```

### Environment Variables

```bash
# OpenAI API key
export OPENAI_API_KEY="sk-..."

# Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."

# For Ollama (local)
# No API key needed, but ensure running: ollama serve
```

### Config Examples

**Minimal Config:**
```yaml
sources:
  - name: "My Source"
    url: "https://example.com"
    scrape_type: "web"

llm:
  provider: "openai"
  model: "gpt-3.5-turbo"
  api_key: "${OPENAI_API_KEY}"
```

**Advanced Config:**
```yaml
sources:
  - name: "Website"
    url: "https://docs.example.com"
    scrape_type: "web"
    content_selector: "main.content"

llm:
  provider: "anthropic"
  model: "claude-3-sonnet-20240229"
  api_key: "${ANTHROPIC_API_KEY}"
  temperature: 0.8

processing:
  chunk_size: 3000
  batch_size: 32
  workers: 4
```

---

**Ready to start?** Run the setup script and follow the "First Run" section above!

For questions, see the full documentation in README.md and CONFIG_GUIDE.md.

# Project Index and File Overview

## Quick Navigation

### 🚀 Getting Started
- **[GETTING_STARTED.md](GETTING_STARTED.md)** - **START HERE!** Complete setup and first-run guide
- **[README.md](README.md)** - Overview, features, and usage examples

### 📚 Documentation
- **[CONFIG_GUIDE.md](CONFIG_GUIDE.md)** - How to configure the pipeline and add data sources
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design, module descriptions, and data flow
- **[RECURSIVE_CRAWLING.md](RECURSIVE_CRAWLING.md)** - Guide for recursive website crawling and link following
- **[PDF_HANDLING.md](PDF_HANDLING.md)** - PDF extraction and automatic format detection guide
- **[RATIONALE.md](RATIONALE.md)** - Design decisions and implementation philosophy

### ⚙️ Setup
- **setup.sh** - Automated setup for Linux/macOS
- **setup.bat** - Automated setup for Windows

### 📋 Configuration
- **config.yaml** - Your configuration file (customize this)
- **config.template.yaml** - Template showing all options

## Core Modules

```
Core Pipeline Modules:
├── main.py                    # CLI entry point and orchestration
├── config.py                  # Configuration loading and validation
├── scraper.py                 # Web content extraction
├── transformer.py             # LLM-based content transformation
├── dataset_generator.py       # Dataset creation (multiple types)
├── jsonl_exporter.py          # JSONL export and validation
└── utils.py                   # Shared utility functions

Configuration:
├── requirements.txt           # Python dependencies
├── config.yaml                # Your configuration (START HERE)
└── config.template.yaml       # Configuration template

Setup:
├── setup.sh                   # Linux/macOS setup script
├── setup.bat                  # Windows setup script
└── .gitignore                 # Git ignore rules
```

## File Descriptions

### Python Modules

#### main.py (370 lines)
**Purpose:** CLI entry point and pipeline orchestration

**Key Functions:**
- `main()` - Main pipeline orchestration
- `validate_arguments()` - CLI argument validation

**Key Classes:** N/A (script-based)

**Responsibilities:**
- Parse command-line arguments
- Load configuration
- Initialize and execute pipeline stages
- Handle errors and logging
- Report completion status

**Usage:**
```bash
python main.py --config config.yaml --output ./datasets
```

---

#### config.py (250+ lines)
**Purpose:** Configuration management and validation

**Key Classes:**
- `ConfigLoader` - YAML configuration loading
- `ValidationError` - Configuration error exception

**Key Methods:**
- `load()` - Load and validate YAML config
- `_validate_sources()` - Validate data sources
- `_validate_llm_config()` - Validate LLM settings
- `_substitute_env_vars()` - Substitute environment variables

**Features:**
- URL format validation
- LLM provider validation
- Environment variable support (${VAR_NAME})
- Comprehensive error messages

---

#### scraper.py (300+ lines)
**Purpose:** Web content extraction

**Key Classes:**
- `WebScraper` - Orchestrates scraping operations
- `ScraperError` - Exception for scraper errors

**Key Methods:**
- `scrape_all()` - Scrape all configured sources
- `_scrape_web()` - Extract HTML content
- `_scrape_pdf()` - Extract PDF text
- `_scrape_api()` - Fetch API data
- `_fetch_url()` - Fetch with retry logic

**Features:**
- Concurrent scraping with ThreadPoolExecutor
- Automatic retry with exponential backoff
- Content cleaning and normalization
- Multiple content types (web, pdf, api)
- CSS selector support

---

#### transformer.py (350+ lines)
**Purpose:** LLM-based content transformation

**Key Classes:**
- `ContentTransformer` - Transforms content using LLM
- `LLMProvider` - Supported provider enum

**Key Methods:**
- `transform_all()` - Transform all content
- `_generate_summary()` - Create summaries
- `_generate_explanation()` - Create explanations
- `_generate_faq()` - Extract Q&A pairs
- `_generate_guide()` - Create step-by-step guides
- `_call_llm()` - LLM API interface

**Supported Providers:**
- OpenAI (GPT-3.5, GPT-4)
- Anthropic (Claude)
- Ollama / Local models

---

#### dataset_generator.py (350+ lines)
**Purpose:** Generate multiple dataset types

**Key Classes:**
- `DatasetGenerator` - Creates datasets
- Multiple dataclasses (InstructionResponsePair, FAQItem, etc.)

**Dataset Types Generated:**
- Instruction-Response pairs (core format)
- Summaries
- FAQs
- Guides
- Explanations
- Multi-turn dialogues

**Key Methods:**
- `generate_instruction_response()` - Core training data
- `generate_summary()` - Summary dataset
- `generate_faq()` - FAQ dataset
- `generate_guide()` - Guide dataset
- `generate_explanation()` - Explanation dataset
- `generate_multi_turn()` - Dialogue dataset

---

#### jsonl_exporter.py (300+ lines)
**Purpose:** JSONL export and validation

**Key Classes:**
- `JSONLExporter` - Exports datasets to JSONL

**Key Methods:**
- `export_all()` - Export all datasets
- `_validate_and_normalize()` - Format validation
- `_combine_datasets()` - Merge datasets
- `_generate_summary()` - Create statistics

**Features:**
- UnSloth/Hugging Face format validation
- Field normalization (instruction, output, input)
- Dataset combination
- Statistical reporting
- Schema validation

---

#### utils.py (200+ lines)
**Purpose:** Shared utility functions

**Key Functions:**
- `setup_logging()` - Configure logging
- `validate_environment()` - Check dependencies
- `ensure_directory()` - Safe directory creation
- `safe_write_file()` - Safe file writing
- `sanitize_filename()` - Clean filenames
- `truncate_text()` - Text truncation
- `format_size()` - Human-readable size
- `count_lines()` - Count lines in file

---

### Documentation Files

#### README.md (250+ lines)
**Contents:**
- Feature overview
- Quick start guide
- Command-line options
- Usage examples
- Training with UnSloth
- Architecture overview
- Troubleshooting

**Best For:** Overview and understanding capabilities

---

#### CONFIG_GUIDE.md (400+ lines)
**Contents:**
- Configuration structure
- Data sources (web, PDF, API)
- LLM provider setup (OpenAI, Anthropic, Ollama)
- Environment variables
- Advanced options
- Configuration examples
- Troubleshooting

**Best For:** Setting up your configuration

---

#### ARCHITECTURE.md (400+ lines)
**Contents:**
- System overview
- Architecture diagram
- Module descriptions
- Complete data flow
- Design patterns
- Key components
- Extension points
- Performance considerations

**Best For:** Understanding system design

---

#### RATIONALE.md (350+ lines)
**Contents:**
- Design philosophy
- Modular architecture rationale
- Configuration approach
- Pipeline design decisions
- LLM integration strategy
- Dataset generation decisions
- Data format choices
- Error handling strategy
- Trade-offs and alternatives

**Best For:** Understanding why design choices were made

---

#### GETTING_STARTED.md (350+ lines)
**Contents:**
- Prerequisites and requirements
- Installation steps
- First run examples
- Output explanation
- Next steps and advanced features
- Comprehensive troubleshooting
- Quick reference and commands

**Best For:** Getting up and running quickly

---

### Configuration Files

#### config.yaml
Your runtime configuration. Customize this file with:
- Data sources to scrape
- LLM provider settings
- Processing parameters

Start by copying `config.template.yaml` or editing directly.

#### config.template.yaml
Template showing all configuration options with:
- Inline documentation
- Examples for each section
- Common configurations
- Best practices

---

### Setup Scripts

#### setup.sh (Linux/macOS)
```bash
chmod +x setup.sh
./setup.sh
```

**Does:**
- Creates Python virtual environment
- Installs dependencies
- Creates config from template
- Creates output directories

#### setup.bat (Windows)
```bash
setup.bat
```

**Does:**
- Creates Python virtual environment
- Installs dependencies
- Creates config from template
- Creates output directories

---

### Other Files

#### requirements.txt
Python package dependencies:
- requests - HTTP client
- beautifulsoup4 - HTML parsing
- pyyaml - YAML parsing
- PyPDF2 - PDF text extraction
- openai - OpenAI API client
- anthropic - Anthropic API client
- ollama - Ollama API client

#### .gitignore
Files to ignore in git:
- `__pycache__/` - Python cache
- `venv/` - Virtual environment
- `config.yaml` - Local configuration
- `datasets/` - Generated output
- `*.log` - Log files
- API keys and environment

---

## Getting Started Path

1. **Start Here:** [GETTING_STARTED.md](GETTING_STARTED.md)
   - Prerequisites check
   - Installation steps
   - First run (5 minutes)

2. **Configure:** [CONFIG_GUIDE.md](CONFIG_GUIDE.md)
   - Edit `config.yaml`
   - Add your data sources
   - Set up LLM provider

3. **Run:** Execute main.py
   ```bash
   python main.py --config config.yaml
   ```

4. **Understand:** Read other documentation
   - [README.md](README.md) - Features and usage
   - [ARCHITECTURE.md](ARCHITECTURE.md) - How it works
   - [RATIONALE.md](RATIONALE.md) - Why design choices

5. **Use Output:** `combined_training_data.jsonl`
   - Use with UnSloth for model fine-tuning
   - Use with Hugging Face Datasets

---

## Pipeline Overview

```
Input: Website URLs (config.yaml)
  ↓
[Scraper] → Extracts raw content
  ↓
[Transformer] → Generates multiple formats using LLM
  ↓
[Dataset Generator] → Creates 6 dataset types
  ↓
[JSONL Exporter] → Validates and exports JSONL
  ↓
Output: combined_training_data.jsonl (ready for training)
```

---

## Statistics

**Total Code:** ~1850 lines of Python
- Modular, well-documented
- Clear separation of concerns
- Comprehensive error handling

**Total Documentation:** ~1500 lines of Markdown
- Module-level docstrings
- Function-level docstrings
- Comprehensive guides

**Files Created:** 18 files
- 7 Python modules
- 6 Markdown documentation files
- 2 Setup scripts
- 3 Configuration files

---

## Quick Commands

```bash
# Setup
./setup.sh              # Linux/macOS
setup.bat              # Windows

# First run (with OpenAI)
export OPENAI_API_KEY="sk-..."
python main.py --config config.yaml

# First run (with Ollama)
ollama serve           # Terminal 1
python main.py --config config.yaml  # Terminal 2

# Generate specific dataset
python main.py --config config.yaml --dataset-type instruction-response

# Debug mode
python main.py --config config.yaml --log-level DEBUG
```

---

## File Sizes (Approximate)

```
main.py                 ~10 KB
config.py             ~10 KB
scraper.py            ~12 KB
transformer.py        ~14 KB
dataset_generator.py  ~14 KB
jsonl_exporter.py     ~12 KB
utils.py              ~8 KB

README.md             ~12 KB
CONFIG_GUIDE.md       ~20 KB
ARCHITECTURE.md       ~20 KB
RATIONALE.md          ~18 KB
GETTING_STARTED.md    ~18 KB

Total: ~178 KB (efficient, highly functional)
```

---

## Next Steps

1. **Run setup.sh or setup.bat** to install everything
2. **Read GETTING_STARTED.md** for first-run guidance
3. **Edit config.yaml** with your data sources
4. **Run the pipeline:** `python main.py --config config.yaml`
5. **Use generated datasets** with UnSloth or Hugging Face

**Questions?** Refer to the documentation files matching your question:
- How to use? → README.md
- How to configure? → CONFIG_GUIDE.md
- How does it work? → ARCHITECTURE.md
- Why designed this way? → RATIONALE.md
- Getting started?→ GETTING_STARTED.md

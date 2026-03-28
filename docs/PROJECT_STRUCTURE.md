# Project Organization Guide

## Project Structure Overview

This project has been reorganized into a modular package structure where related code is grouped into focused subdirectories.

### Core Packages

**`config/`** - Configuration Management
- `config.py` - Configuration loader and validator
- `config.yaml` - Active runtime configuration
- `config.template.yaml` - Template for new configurations
- `CONFIG_GUIDE.md` - Comprehensive configuration documentation

**`scraper/`** - Web Content Extraction
- `scraper.py` - Web scraping implementation
- `RECURSIVE_CRAWLING.md` - Details on recursive crawling capabilities
- `PDF_HANDLING.md` - PDF text extraction documentation

**`transform/`** - LLM-Based Content Transformation
- `transformer.py` - Content transformation implementation
- Uses multiple LLM providers: OpenAI, Anthropic, Ollama

**`generate/`** - Dataset Generation
- `dataset_generator.py` - Generates training datasets in multiple formats
- Supports: instruction-response, FAQ, summaries, guides, explanations, multi-turn dialogues

**`export/`** - Data Export
- `jsonl_exporter.py` - Exports datasets to JSONL format
- Compatible with UnSloth and Hugging Face

**`utils_module/`** - Shared Utilities
- `utils.py` - Common helper functions
- Logging, validation, file operations

**`examples/`** - Usage Examples
- `examples.py` - Complete code examples
- Demonstrates library usage and integration patterns

### Root Level Files (Entry Points)

- `main.py` - CLI orchestrator for the entire pipeline
- `requirements.txt` - Python dependencies
- `README.md` - Project overview
- `GETTING_STARTED.md` - Quick start guide (in root for easy access)

### Documentation

Documentation files are organized as follows:

**`docs/`** Folder (High-Level Documentation)
- `ARCHITECTURE.md` - System design and data flow
- `RATIONALE.md` - Design decisions and justifications
- `IMPLEMENTATION_NOTES.md` - Implementation details
- `PROJECT_INDEX.md` - This file

**Package-Specific Documentation**
- `config/CONFIG_GUIDE.md` - Configuration reference
- `scraper/RECURSIVE_CRAWLING.md` - Web crawling guide
- `scraper/PDF_HANDLING.md` - PDF extraction guide

### Output Directories

- `datasets/` - Generated training datasets
- `raw_content/` - Raw scraped content
- `transformed_content/` - LLM-transformed content

## Import Patterns

All modules can be imported cleanly from their packages:

```python
# Configuration
from config import ConfigLoader, ValidationError

# Web Scraping
from scraper import WebScraper, ScraperError

# Content Transformation
from transform import ContentTransformer, LLMProvider

# Dataset Generation
from generate import DatasetGenerator

# Data Export
from export import JSONLExporter

# Utilities
from utils_module import setup_logging, validate_environment
```

## Removed Duplicate Files

The following root-level files have been superseded by the package version and can be safely deleted:

- ~~`config.py`~~ → `config/config.py`
- ~~`config.yaml`~~ → `config/config.yaml`
- ~~`config.template.yaml`~~ → `config/config.template.yaml`
- ~~`scraper.py`~~ → `scraper/scraper.py`
- ~~`transformer.py`~~ → `transform/transformer.py`
- ~~`dataset_generator.py`~~ → `generate/dataset_generator.py`
- ~~`jsonl_exporter.py`~~ → `export/jsonl_exporter.py`
- ~~`utils.py`~~ → `utils_module/utils.py`
- ~~`examples.py`~~ → `examples/examples.py`

## Migration Guide

### If you were importing from root directly:

**Before:**
```python
from scraper import WebScraper
from transformer import ContentTransformer
from dataset_generator import DatasetGenerator
from utils import setup_logging
```

**After (use imports from packages):**
```python
from scraper import WebScraper
from transform import ContentTransformer
from generate import DatasetGenerator
from utils_module import setup_logging
```

### Running the CLI

The CLI usage remains the same:

```bash
python main.py --config config/config.yaml
```

### Configuration File References

The default config path in main.py has been updated to: `config/config.yaml`

If you're using a custom config path, ensure it points to the correct location.

## Benefits of This Organization

1. **Modularity** - Each package has a clear, single responsibility
2. **Discoverability** - Related code and documentation grouped together
3. **Maintainability** - Easy to locate and update specific functionality
4. **Testability** - Package structure supports isolated unit testing
5. **Scalability** - Easy to add new transformation types, scrapers, etc.
6. **Documentation** - Docs co-located with their respective packages

## Adding New Modules

To add a new capability (e.g., a new scraper type or LLM provider):

1. **Create a new package**: `mkdir new_feature`
2. **Add package files**: `new_feature/__init__.py`, `new_feature/implementation.py`
3. **Add documentation**: `new_feature/README.md` or `docs/NEW_FEATURE_GUIDE.md`
4. **Update imports**: Export classes in `__init__.py`
5. **Integrate in main.py**: Add imports and logic to orchestrator

## File Tree

```
AutoTrain/
├── main.py                              # CLI entry point
├── README.md                            # Project overview
├── GETTING_STARTED.md                   # Quick start
├── requirements.txt                     # Dependencies
├── setup.bat                            # Windows setup
├── setup.sh                             # Unix setup
│
├── config/                              # Configuration package
│   ├── __init__.py
│   ├── config.py
│   ├── config.yaml
│   ├── config.template.yaml
│   └── CONFIG_GUIDE.md
│
├── scraper/                             # Web scraper package
│   ├── __init__.py
│   ├── scraper.py
│   ├── RECURSIVE_CRAWLING.md
│   └── PDF_HANDLING.md
│
├── transform/                           # LLM transformation package
│   ├── __init__.py
│   ├── transformer.py
│   └── (guide docs)
│
├── generate/                            # Dataset generation package
│   ├── __init__.py
│   ├── dataset_generator.py
│   └── (guide docs)
│
├── export/                              # Data export package
│   ├── __init__.py
│   ├── jsonl_exporter.py
│   └── (guide docs)
│
├── utils_module/                        # Utilities package
│   ├── __init__.py
│   └── utils.py
│
├── examples/                            # Examples package
│   ├── __init__.py
│   └── examples.py
│
├── docs/                                # High-level documentation
│   ├── ARCHITECTURE.md
│   ├── RATIONALE.md
│   ├── IMPLEMENTATION_NOTES.md
│   └── PROJECT_INDEX.md
│
├── datasets/                            # Output: Generated datasets
├── raw_content/                         # Output: Raw scraped content
└── transformed_content/                 # Output: Transformed content
```

## Next Steps

1. **Verify Installation**: `python main.py --help`
2. **Run Examples**: See `examples/examples.py`
3. **Configure**: Edit `config/config.yaml`
4. **Run Pipeline**: `python main.py --config config/config.yaml`

Questions? See the package-specific documentation in each folder.

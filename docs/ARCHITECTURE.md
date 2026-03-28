# Architecture and Design Documentation

This document provides a detailed overview of the LLM Training Data Generator's architecture, module interactions, and data flow.

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Module Descriptions](#module-descriptions)
4. [Data Flow](#data-flow)
5. [Design Patterns](#design-patterns)
6. [Key Components](#key-components)
7. [Extension Points](#extension-points)

## System Overview

The LLM Training Data Generator is a modular pipeline that transforms raw web content into structured training datasets through these stages:

```
Configuration Loading → Content Scraping → LLM Transformation → Dataset Generation → JSONL Export
```

**Design Principles:**
- **Modularity**: Each stage is independent and can be skipped
- **Extensibility**: Easy to add new data sources and dataset types
- **Robustness**: Error handling and retry logic throughout
- **Efficiency**: Concurrent processing where applicable
- **Traceability**: Comprehensive logging at all steps

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                        CLI Entry Point                          │
│                        (main.py)                                │
│                                                                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   ┌─────────┐  ┌──────────┐  ┌──────────┐
   │  Config │  │ Logging  │  │ Validation│
   │ Loader  │  │  Setup   │  │ Helpers  │
   │(config.py)│ (utils.py)│  │(utils.py)│
   └────┬────┘  └──────────┘  └──────────┘
        │
        │ Configuration
        ▼
   ┌──────────────────────────────────────┐
   │       Web Scraper Module             │
   │      (scraper/ package)              │
   │  - HTML extraction                   │
   │  - PDF extraction                    │
   │  - API fetching                      │
   │  - Concurrent workers                │
   │  - Retry logic                       │
   └──────┬───────────────────────────────┘
          │ Raw Content (JSON)
          ▼
   [Raw Content Directory]
          │
          │
        ▼
   ┌──────────────────────────────────────┐
   │  Content Transformer Module          │
   │      (transformer.py)                │
   │  - LLM Provider Support              │
   │    • OpenAI / Claude / Ollama       │
   │  - Content Chunking                  │
   │  - Transformation Types:             │
   │    • Summarization                  │
   │    • Explanation Generation          │
   │    • FAQ Extraction                 │
   │    • Guide Creation                 │
   └──────┬───────────────────────────────┘
          │ Transformed Content (JSON)
          ▼
   [Transformed Content Directory]
          │
          │
        ▼
   ┌──────────────────────────────────────┐
   │  Dataset Generator Module            │
   │   (dataset_generator.py)             │
   │  Generates multiple formats:         │
   │  - Instruction-Response              │
   │  - Summaries                         │
   │  - FAQs                              │
   │  - Guides                            │
   │  - Explanations                      │
   │  - Multi-turn Dialogues              │
   └──────┬───────────────────────────────┘
          │ Raw Datasets (JSONL)
          ▼
   [Datasets Directory]
          │
          │
        ▼
   ┌──────────────────────────────────────┐
   │    JSONL Exporter Module             │
   │     (jsonl_exporter.py)              │
   │  - Format Validation                 │
   │  - UnSloth Compatibility             │
   │  - Dataset Combination               │
   │  - Statistics Generation             │
   └──────┬───────────────────────────────┘
          │
          ▼
   ┌──────────────────────────────────────┐
   │   Final Datasets (JSONL)             │
   │  - combined_training_data.jsonl      │
   │  - instruction_response.jsonl        │
   │  - summary.jsonl                     │
   │  - faq.jsonl                         │
   │  - guide.jsonl                       │
   │  - explanation.jsonl                 │
   │  - multi_turn.jsonl                  │
   │  - DATASET_SUMMARY.md                │
   └──────────────────────────────────────┘
```

## Module Descriptions

### 1. main.py - CLI Orchestration

**Purpose:** Entry point and workflow orchestration

**Key Responsibilities:**
- Parse command-line arguments
- Initialize pipeline components
- Execute pipeline stages sequentially
- Handle errors and logging
- Report completion status

**Class:** N/A (script-based)

**Key Functions:**
- `main()` - Pipeline orchestration
- `validate_arguments()` - CLI argument validation

### 2. config.py - Configuration Management

**Purpose:** Load and validate pipeline configuration

**Key Classes:**
- `ConfigLoader` - Loads YAML configuration
- `ValidationError` - Configuration error exception

**Key Responsibilities:**
- Parse YAML configuration files
- Validate source URLs and LLM configuration
- Support environment variable substitution
- Provide comprehensive error messages

**Features:**
- URL format validation
- Scrape type verification
- LLM provider validation
- Environment variable interpolation

### 3. scraper/ - Web Content Extraction

**Purpose:** Extract content from various web sources with automatic format detection

**Location:** `scraper/` package (scraper/__init__.py, scraper/scraper.py)

**Key Classes:**
- `WebScraper` - Orchestrates scraping operations
- `ScraperError` - Scraper error exception

**Key Methods:**
- `scrape_all()` - Scrape all configured sources concurrently
- `scrape_source()` - Scrape individual source with format detection
- `_scrape_web()` - Extract HTML content (with PDF auto-detection)
- `_scrape_pdf()` - Extract text from PDF documents
- `_scrape_api()` - Fetch JSON API data
- `_is_pdf_url()` - Detect PDFs served as HTML
- `_crawl_recursive()` - Follow links recursively with depth control
- `_extract_links()` - Extract same-domain links from HTML

**Features:**
- Concurrent scraping with ThreadPoolExecutor
- **Automatic PDF detection** (even when served as HTML URLs)
  - Checks Content-Type header for "application/pdf"
  - Falls back to URL extension checking (.pdf)
  - Intelligently routes to PDF parser when detected
- Recursive website crawling with configurable depth
- Same-domain link filtering with www. normalization
- Automatic retry logic with exponential backoff
- Rate limiting between requests (configurable delay)
- URL deduplication in recursive mode
- Content cleaning and normalization
- Source metadata preservation
- CSS selector support for HTML content extraction

**Output Format:**
```json
{
    "metadata": {
        "name": "Source Name",
        "url": "https://...",
        "scrape_type": "web|pdf|api",
        "scraped_at": "2024-01-01 12:00:00",
        "content_length": 5000
    },
    "content": "..."
}
```

### 4. transformer.py - LLM Content Transformation

**Purpose:** Transform raw content using LLM

**Key Classes:**
- `ContentTransformer` - Orchestrates transformations
- `LLMProvider` - Enum of supported providers

**Key Methods:**
- `transform_all()` - Transform all content
- `_transform_file()` - Transform single file
- `_chunk_content()` - Split content into chunks
- `_generate_summary()` - Create summarizations
- `_generate_explanation()` - Create explanations
- `_generate_faq()` - Extract Q&A pairs
- `_generate_guide()` - Create step-by-step guides
- `_call_llm()` - LLM API interface

**Supported Providers:**
- OpenAI (GPT-3.5, GPT-4)
- Anthropic (Claude models)
- Ollama / Local models
- Future extensibility

**Output Format:**
```json
{
    "metadata": {...},
    "transformations": {
        "summaries": ["...", "..."],
        "explanations": ["...", "..."],
        "faqs": [
            {"question": "...", "answer": "..."}
        ],
        "guides": [
            {"title": "...", "steps": [...]}
        ]
    }
}
```

### 5. dataset_generator.py - Dataset Creation

**Purpose:** Generate multiple dataset types from transformed content

**Key Classes:**
- `DatasetGenerator` - Creates different dataset types
- `InstructionResponsePair` - Data class for instruction-response
- `FAQItem` - Data class for FAQ
- `GuideItem` - Data class for guides
- `ExplanationItem` - Data class for explanations
- `MultiTurnDialogue` - Data class for dialogues

**Key Methods:**
- `generate_instruction_response()` - Core training format
- `generate_summary()` - Summary dataset
- `generate_faq()` - FAQ dataset
- `generate_guide()` - Guide dataset
- `generate_explanation()` - Explanation dataset
- `generate_multi_turn()` - Dialogue dataset
- `_save_dataset()` - Save to JSONL format

**Output Formats:**
Each dataset type generates JSONL with structured fields:
```json
{
    "instruction": "...",
    "input": "...",
    "output": "...",
    "category": "..."
}
```

### 6. jsonl_exporter.py - JSONL Export

**Purpose:** Export and validate datasets in JSONL format

**Key Classes:**
- `JSONLExporter` - Orchestrates JSONL export

**Key Methods:**
- `export_all()` - Export all datasets
- `_export_single()` - Export individual file
- `_validate_and_normalize()` - Format validation
- `_combine_datasets()` - Merge datasets
- `_generate_summary()` - Create statistics

**Features:**
- UnSloth/Hugging Face format validation
- Field normalization (instruction, output, input)
- Data combination
- Statistical reporting
- Schema validation

### 7. utils.py - Utility Functions

**Purpose:** Shared utility functions

**Key Functions:**
- `setup_logging()` - Configure logging
- `validate_environment()` - Check dependencies
- `ensure_directory()` - Create directories safely
- `safe_write_file()` - Write files with error handling
- `sanitize_filename()` - Clean filenames
- `truncate_text()` - Text truncation
- `format_size()` - Human-readable sizes

## Data Flow

### Complete Pipeline Flow

```
1. CLI Invocation (main.py)
   ↓
2. Configuration Loading (config.py)
   ├─ Parse YAML
   ├─ Validate structure
   └─ Substitute environment variables
   ↓
3. Environment Validation (utils.py)
   ├─ Check Python version
   └─ Verify dependencies
   ↓
4. Web Scraping (scraper/ package)
   ├─ Create ThreadPoolExecutor (N workers)
   ├─ For each source:
   │  ├─ Fetch content
   │  ├─ Extract/clean text
   │  └─ Save to disk
   └─ Outputs: raw_content/*.json
   ↓
5. Content Transformation (transformer.py)
   ├─ Load raw content files
   ├─ Initialize LLM client
   ├─ For each file:
   │  ├─ Split into chunks
   │  ├─ Generate summaries
   │  ├─ Generate explanations
   │  ├─ Extract FAQs
   │  └─ Generate guides
   └─ Outputs: transformed/*.json
   ↓
6. Dataset Generation (dataset_generator.py)
   ├─ Load transformed content
   ├─ Create multiple dataset types:
   │  ├─ Instruction-Response pairs
   │  ├─ Summaries
   │  ├─ FAQs
   │  ├─ Guides
   │  ├─ Explanations
   │  └─ Multi-turn dialogues
   └─ Outputs: datasets/*.jsonl
   ↓
7. JSONL Export & Validation (jsonl_exporter.py)
   ├─ Validate each item
   ├─ Normalize format
   ├─ Combine datasets
   ├─ Generate statistics
   └─ Outputs: final_*.jsonl, combined_training_data.jsonl
```

### Data Transformation Examples

**Web Content → Instruction-Response Pairs:**
```
Raw: "Python is a high-level programming language..."
↓ (LLM Processing)
Instruction: "What is Python?"
Output: "Python is a high-level programming language..."
```

**Article → Multi-turn Dialogue:**
```
Raw: Complex article about machine learning
↓ (LLM Processing)
User: "What is machine learning?"
Assistant: "Machine learning is..."
User: "How does it differ from AI?"
Assistant: "AI is broader..."
```

**Content → FAQ:**
```
Raw: Technical documentation
↓ (LLM Processing)
Q: "How do I get started?"
A: "First, install the library..."
Q: "What are the requirements?"
A: "You need Python 3.8+..."
```

## Design Patterns

### 1. Pipeline Pattern
- Sequential stages with optional skipping
- Each stage outputs data for next stage
- Clean separation of concerns

### 2. Builder Pattern
- `DatasetGenerator` constructs multiple dataset types
- Each method builds specific dataset format

### 3. Adapter Pattern
- `ContentTransformer` adapts to different LLM providers
- Abstracts provider-specific APIs

### 4. Strategy Pattern
- Different scraping strategies (web, PDF, API)
- Each implements `_scrape_*` method

### 5. Batch Processing Pattern
- ThreadPoolExecutor for concurrent scraping
- Batch LLM processing for efficiency

## Key Components

### Configuration System

**Feature:** YAML-based, schema-validated configuration

**Files:**
- `config/config.yaml` - Runtime configuration
- `config.template.yaml` - Template for users

**Features:**
- Environment variable support: `${VAR_NAME}`
- Automatic validation
- Comprehensive error messages

### Logging System

**Feature:** Comprehensive logging at all stages

**Levels:**
- DEBUG: Detailed execution info
- INFO: Major operations and progress
- WARNING: Recoverable errors, issues
- ERROR: Unrecoverable errors

**Output:** Console + optional file logging

**Example:**
```
2024-01-15 10:30:45 - root - INFO - WebScraper initialized with 2 workers
2024-01-15 10:30:46 - root - INFO - Successfully scraped: Python Documentation
```

### Error Handling

**Strategy:** Graceful degradation with clear error messages

**Exceptions:**
- `ValidationError` - Configuration issues
- `ScraperError` - Scraping failures
- Generic `Exception` - Unexpected errors

**Features:**
- Retry logic for network failures
- Partial success handling
- Detailed error reporting

### Concurrency

**Strategy:** ThreadPoolExecutor for I/O-bound operations

**Applications:**
- Web scraping (network I/O)
- File writing
- API calls

**Configuration:**
- `--workers N` for scraping concurrency
- `--batch-size N` for LLM batch processing

## Extension Points

### 1. Adding New Scraper Types

Add new method in `scraper/scraper.py`:

```python
def _scrape_custom(self, source: Dict[str, Any]) -> None:
    # Implementation
    content = self._fetch_custom(source['url'])
    self._save_source_content(source, content, 'custom')
```

Update `scrape_source()` switch statement.

### 2. Adding New LLM Providers

Update `transformer.py`:

```python
def _initialize_llm_client(self) -> None:
    if provider == 'gemini':
        from google import genai
        self.client = genai.Client(api_key=...)
```

Implement `_call_llm()` provider logic.

### 3. Adding New Dataset Types

Add method in `dataset_generator.py`:

```python
def generate_new_type(self) -> None:
    items = []
    # Generation logic
    self._save_dataset('new_type', items)
```

### 4. Custom Output Formats

Extend `jsonl_exporter.py`:

```python
def export_custom_format(self) -> None:
    # Custom serialization logic
    pass
```

### 5. New Utilities

Add functions to `utils.py` for reuse across modules:

```python
def custom_utility(param: str) -> str:
    """Detailed docstring."""
    # Implementation
    pass
```

## Performance Considerations

### Scraping Optimization
- Increase workers: faster but more network load
- Balance: 2-4 workers recommended

### LLM Processing
- Larger chunks = fewer API calls but potential quality loss
- Batch processing improves efficiency
- Local models (Ollama) faster than API calls

### Memory Usage
- Reduce batch size: lower memory but slower
- Process in stages: scrape → transform → generate

### Storage
- Raw content: ~1-5MB per source
- Transformed content: ~2-10MB per source
- Final datasets: ~0.5-2MB per source
- Total: Estimate 10-20x input content size

## Testing and Quality

### Validation Points
- Configuration validation (config.py)
- URL format validation (config.py)
- JSONL format validation (jsonl_exporter.py)
- Data schema validation (dataset_generator.py)

### Logging for Debugging
- Enable DEBUG logging: `--log-level DEBUG`
- Check log messages for:
  - Source accessibility
  - LLM success/failure rates
  - Dataset generation counts
  - Format issues

## Next Steps

For more information:
- See [README.md](README.md) for usage
- See [CONFIG_GUIDE.md](CONFIG_GUIDE.md) for configuration
- See [RATIONALE.md](RATIONALE.md) for design decisions

# LLM Training Data Generator

An intelligent, modular Python pipeline for automatically generating diverse training datasets for fine-tuning open-source LLMs using UnSloth. This tool transforms raw web content into multiple structured dataset formats compatible with industry-standard LLM training frameworks.

## Features

### 📊 Multiple Dataset Types
- **Instruction-Response Pairs**: Core format for instruction-following training
- **Summaries**: Extract and generate concise content summaries
- **Explanations**: Detailed explanations and conceptual breakdowns
- **FAQs**: Question-answer pairs for knowledge-based training
- **Step-by-Step Guides**: Procedural and tutorial content
- **Multi-turn Dialogues**: Realistic conversation flows for dialogue models

### 🌐 Flexible Content Sources
- HTML web pages with CSS selector targeting
- **PDF documents** (including auto-detection of PDFs served as HTML)
- RESTful APIs
- **Recursive website crawling** with configurable depth and page limits
- Concurrent scraping with configurable workers
- Automatic format detection with intelligent routing

### 🤖 LLM Provider Support
- **OpenAI**: GPT-3.5, GPT-4, and newer models
- **Anthropic**: Claude models (opus, sonnet, haiku)
- **Local/Ollama**: Self-hosted open models (Llama, Mistral, etc.)

### 📦 UnSloth-Compatible Output
- JSONL format suitable for UnSloth and Hugging Face
- Standardized schema for all dataset types
- Combined training data file for batch processing
- Dataset statistics and summary reports

## Quick Start

### 1. Installation

```bash
# Clone or download the project
cd AutoTrain

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create or edit `config/config.yaml` with your data sources:

```yaml
sources:
  - name: "Python Documentation"
    url: "https://docs.python.org/3/"
    scrape_type: "web"
    content_selector: "main"

llm:
  provider: "openai"
  model: "gpt-3.5-turbo"
  api_key: "${OPENAI_API_KEY}"
```

See [CONFIG_GUIDE.md](CONFIG_GUIDE.md) for detailed configuration options.

### 3. Run the Pipeline

```bash
# Generate all dataset types
python main.py --config config/config.yaml --output ./datasets

# Generate specific dataset type
python main.py --config config/config.yaml --dataset-type instruction-response

# Skip scraping (use existing content)
python main.py --config config/config.yaml --skip-scrape

# Use local LLM (Ollama)
python main.py --config config/config.yaml --workers 4
```

### 4. Output Files

The pipeline creates the following structure:

```
datasets/
├── raw_content/          # Original scraped content (JSON)
├── transformed/          # LLM-transformed content (JSON)
├── datasets/             # Individual JSONL files per type
│   ├── instruction_response.jsonl
│   ├── summary.jsonl
│   ├── faq.jsonl
│   ├── guide.jsonl
│   ├── explanation.jsonl
│   └── multi_turn.jsonl
├── combined_training_data.jsonl
└── DATASET_SUMMARY.md    # Statistics and usage guide
```

## Command-Line Options

```bash
python main.py [OPTIONS]

Options:
  --config CONFIG_PATH              Path to configuration file (default: config/config.yaml)
  --output OUTPUT_DIR               Output directory (default: ./datasets)
  --dataset-type {all|instruction-response|summary|faq|guide|explanation|multi-turn}
                                     Dataset type to generate (default: all)
  --workers N                        Concurrent workers for scraping (default: 2)
  --batch-size N                     Batch size for LLM processing (default: 16)
  --log-level {DEBUG|INFO|WARNING|ERROR}
                                     Logging level (default: INFO)
  --skip-scrape                     Skip web scraping phase
  --skip-transform                  Skip LLM transformation phase
```

## Smart Content Detection

The scraper includes **automatic format detection** for seamless content extraction:

### Automatic PDF Detection

The system intelligently detects PDFs even when served as regular HTML URLs:

- **Content-Type Detection**: Checks HTTP headers for "application/pdf"
- **Extension Fallback**: Falls back to URL extension checking (.pdf)
- **Smart Routing**: Automatically uses PDF text extraction when detected
- **Transparent**: Works without requiring manual `scrape_type: "pdf"` configuration

```yaml
sources:
  # This will automatically detect and extract text from the PDF
  - name: "Documentation PDF"
    url: "https://example.com/docs/file"  # No .pdf extension!
    scrape_type: "web"
    content_selector: "main"
```

The above will still work correctly even if the URL serves a PDF document.

### Recursive Crawling with Page Limits

For comprehensive dataset creation from entire websites, enable recursive crawling with optional page limiting:

```yaml
sources:
  - name: "Full Documentation"
    url: "https://docs.example.com"
    scrape_type: "web"
    recursive: true
    crawl_depth: 3        # Up to 3 levels deep
    max_pages: 100        # But stop at 100 pages total
```

Key features:
- **Configurable Depth**: Control nesting levels (1=single page, 3-4=typical, 5+=very deep)
- **Page Limiting**: Set maximum pages per source or use "max" for unlimited
- **Per-source Control**: Override global settings for specific sources
- **Deduplication**: Automatic URL deduplication prevents duplicate processing
- **Same-domain Filtering**: Only follows internal links, prevents external crawling

See [RECURSIVE_CRAWLING.md](RECURSIVE_CRAWLING.md) for comprehensive recursive crawling documentation.

## Usage Examples

### Example 1: Complete Pipeline with OpenAI

```bash
# Set API key
export OPENAI_API_KEY="sk-..."

# Run full pipeline
python main.py --config config/config.yaml --output ./training_data --log-level INFO
```

### Example 2: Using Local Ollama LLM

```bash
# Update config/config.yaml to use ollama
# Then run:
python main.py --config config/config.yaml --workers 4
```

### Example 3: Generate Specific Dataset Type

```bash
# Only generate instruction-response pairs
python main.py --config config/config.yaml --dataset-type instruction-response

# Generate FAQ and guide datasets
python main.py --config config/config.yaml --dataset-type faq
python main.py --config config/config.yaml --dataset-type guide
```

### Example 4: Iterate on Existing Content

```bash
# Skip scraping to reprocess existing content with different settings
python main.py --config config/config.yaml --skip-scrape --dataset-type all
```

## Training with UnSloth

Once you have generated your JSONL files, you can fine-tune a model with UnSloth:

```python
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer

# Load the generated dataset
dataset = load_dataset('json', data_files='datasets/combined_training_data.jsonl')

# Initialize model with UnSloth optimizations
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="unsloth/mistral-7b-bnb-4bit",
    max_seq_length=2048,
    load_in_4bit=True,
    dtype=None,
)

# Fine-tune
trainer = SFTTrainer(
    model=model,
    train_dataset=dataset['train'],
    max_seq_length=2048,
    dataset_text_field='instruction',
    args=TrainingArguments(
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        warmup_steps=5,
        num_train_epochs=1,
        learning_rate=2e-4,
        output_dir='output',
        optim='paged_adamw_8bit',
    ),
)

trainer.train()
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed documentation of the system design, module interactions, and data flow.

## Design Rationale

See [RATIONALE.md](RATIONALE.md) for detailed explanations of key design decisions and implementation approaches.

## Configuration Guide

See [CONFIG_GUIDE.md](CONFIG_GUIDE.md) for comprehensive configuration documentation including:
- How to add new web sources
- LLM provider setup
- Fine-tuning generation parameters
- Environment variable usage

## Project Structure

```
AutoTrain/
├── main.py                        # CLI entry point and orchestration
├── transformer.py                 # LLM-based content transformation
├── dataset_generator.py           # Dataset creation from transformed content
├── jsonl_exporter.py              # JSONL output and formatting
├── utils.py                       # Shared utility functions
├── requirements.txt               # Python dependencies
├── config/                        # Configuration package
│   ├── __init__.py               # Package initialization
│   ├── config.py                 # Configuration loader
│   ├── config.yaml               # Runtime configuration
│   └── config.template.yaml      # Configuration template
├── scraper/                       # Web scraper package
│   ├── __init__.py               # Package initialization
│   └── scraper.py                # Web content extraction
├── datasets/                      # Generated datasets directory
├── raw_content/                   # Raw scraped content
├── transformed_content/           # Transformed content by LLM
├── README.md                      # This file
├── CONFIG_GUIDE.md                # Configuration documentation
├── ARCHITECTURE.md                # System design documentation
└── RATIONALE.md                   # Design decisions and rationale
```

## Troubleshooting

### Missing Dependencies
```bash
pip install -r requirements.txt
```

### API Key Issues
```bash
# For OpenAI
export OPENAI_API_KEY="your-key-here"

# For Anthropic
export ANTHROPIC_API_KEY="your-key-here"
```

### Scraping Failures
- Check URLs are accessible
- Verify CSS selectors are correct
- Increase timeout: `--workers 1` for slower connections

### LLM Connection Issues
- Verify API keys are correct
- Check rate limits
- For Ollama: ensure service is running on correct host

## Performance Tips

1. **Adjust Workers**: Increase `--workers` for faster scraping (2-4 recommended)
2. **Batch Size**: Smaller batches (8-16) for lower memory, larger (32+) for speed
3. **Skip Phases**: Use `--skip-scrape` or `--skip-transform` to reprocess data
4. **Local LLMs**: Use Ollama for privacy and cost savings over API calls

## License

MIT License - Feel free to use and modify for your needs.

## Contributing

Contributions welcome! Please ensure:
- Code follows project structure and conventions
- All functions have docstrings
- New features include documentation updates
- Configuration changes follow YAML schema

## Support

For issues or questions:
1. Check [CONFIG_GUIDE.md](CONFIG_GUIDE.md) for configuration help
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for design overview
3. Check troubleshooting section above

# PDF Extraction and Handling Guide

## Overview

The LLM Training Data Generator includes sophisticated PDF handling capabilities with automatic format detection. Whether you have PDFs served as standard URLs, with .pdf extensions, or disguised as HTML, the system intelligently detects and extracts text content.

## Automatic PDF Detection

### How It Works

When scraping a URL configured as `scrape_type: "web"`, the system performs intelligent detection:

```
URL Request
    ↓
Check HTTP Content-Type Header
    ↓
    ├─ If "application/pdf" → Route to PDF extractor
    ├─ If HTML type → Continue to HTML parsing
    └─ If unknown → Check URL extension
        ↓
        ├─ If ends with .pdf → Route to PDF extractor
        └─ Otherwise → Parse as HTML
```

### Detection Methods

#### 1. Content-Type Header Detection

**Most reliable method** - Checks the HTTP response headers:

```
GET /documents/file HTTP/1.1
...
Response Headers:
Content-Type: application/pdf
```

- Efficient: Uses HEAD request without downloading full content
- Reliable: Server explicitly identifies content type
- Works even with non-.pdf URLs (e.g., `/docs/file.pdf?v=2`)

#### 2. URL Extension Detection

**Fallback method** - Examines the URL:

```
https://example.com/guide.pdf     ✓ Detected as PDF
https://example.com/docs.pdf      ✓ Detected as PDF
https://example.com/PDF/file      ✓ Detected as PDF (case-insensitive)
https://example.com/file          ✗ Not detected, parsed as HTML
```

- Works for simple .pdf URLs
- Case-insensitive checking
- Fallback when Content-Type unavailable

## Configuration Options

### Simple PDF Configuration

```yaml
sources:
  - name: "User Guide"
    url: "https://example.com/guide.pdf"
    scrape_type: "pdf"
```

### HTML URL with Auto-Detection

```yaml
sources:
  - name: "Product Overview"
    url: "https://example.com/documents/overview"
    scrape_type: "web"
    # System automatically detects if this serves a PDF
```

### Multiple PDFs in One Source

```yaml
sources:
  - name: "Research Papers"
    url: "https://example.com/papers/collection.pdf"
    scrape_type: "pdf"
```

## PDF Text Extraction

### How It Works

1. **Download**: Fetches PDF from URL with retry logic (3 attempts default)
2. **Parse**: Loads PDF using PyPDF2 library
3. **Extract**: Reads text from each page sequentially
4. **Clean**: Normalizes whitespace and line endings
5. **Save**: Stores extracted text with metadata

### Page-by-Page Extraction

The system extracts text from every page in the PDF:

```python
# Each page content is extracted and joined
Page 1 content
Page 2 content
Page 3 content
...
All joined with newlines
```

### Text Quality

- **What works well**:
  - Standard PDF documents with searchable text
  - Reports, papers, documentation
  - eBooks and guides (text-based PDFs)

- **What has limitations**:
  - Scanned image PDFs (no OCR support)
  - Complex layouts with multiple columns
  - Forms and formatted tables (limited structure preservation)
  - Embedded graphics and charts (ignored)

**Note**: If you need OCR for scanned PDFs, consider preprocessing with dedicated OCR tools before using this system.

## Error Handling

### Common Issues

#### Issue: "Failed to extract text from page X"

**Cause**: Corrupted page or unusual PDF format

**Solution**:
- PDF still processes other pages
- Check PDF integrity with external PDF tools
- Try extracting with different PDF reader if repeatable

#### Issue: Empty or minimal text extracted

**Cause**: Scanned image PDF (no OCR)

**Solution**:
- Use OCR tool to convert to searchable PDF first
- Consider alternative data source
- Pre-process with PyTorch/OpenCV if feasible

#### Issue: 403 Forbidden when fetching PDF

**Cause**: Server blocking automated access

**Solution**:
```yaml
# Add User-Agent consideration (already included)
# If still blocked, consider:
# - Downloading manually and hosting locally
# - Using direct URL if redirect-free version exists
# - Checking site's Terms of Service
```

## Configuration Best Practices

### 1. Consistent Naming

```yaml
sources:
  - name: "API Documentation PDF"
    url: "https://docs.example.com/api-ref.pdf"
    scrape_type: "pdf"
```

Clear naming helps in output file organization.

### 2. Content Selectors (Not Used for PDFs)

```yaml
sources:
  - name: "User Guide"
    url: "https://example.com/guide.pdf"
    scrape_type: "pdf"
    # content_selector is ignored for PDFs
```

CSS selectors only apply to HTML extraction.

### 3. Mix HTML and PDF Sources

```yaml
sources:
  - name: "Documentation"
    url: "https://docs.example.com/guide.html"
    scrape_type: "web"
    content_selector: "article"
  
  - name: "API Reference"
    url: "https://docs.example.com/api.pdf"
    scrape_type: "pdf"
  
  - name: "Quick Start"
    url: "https://example.com/quickstart"  # Auto-detected as PDF
    scrape_type: "web"
```

Mix sources freely - each is processed appropriately.

### 4. Large PDF Handling

```yaml
processing:
  chunk_size: 1500  # Smaller chunks for PDF content
  workers: 2        # Reduce concurrent workers if memory-heavy
```

Large PDFs (100+ pages) may benefit from reduced chunk sizes.

## Output Files

### Single PDF Source

Input:
```yaml
- name: "User Guide"
  url: "https://example.com/guide.pdf"
  scrape_type: "pdf"
```

Output:
```
raw_content/
└── user_guide_pdf.json  # All pages combined
```

### Recursive Crawl with PDFs

If a website contains links to PDFs:

```
raw_content/
├── documentation_web_abc123.json  # HTML page 1
├── documentation_web_def456.json  # HTML page 2
└── documentation_web_guide.json   # Link to PDF (auto-detected)
```

## Dataset Generation from PDFs

### Datasets Created

From PDF text, the system generates:

1. **Summaries**: Concise document summaries
2. **FAQs**: Question-answer pairs extracted from content
3. **Explanations**: Detailed explanations of topics
4. **Guides**: Step-by-step guides if procedural content
5. **Instruction-Response**: General instruction pairs
6. **Multi-turn Dialogues**: Conversational turns

### Example

**PDF Content (Page 1):**
```
Configuration Guide

1. Installation
   - Download from example.com
   - Run installer

2. Basic Setup
   - Create config file
   - Set environment variables
```

**Generated Datasets:**

Summary:
```json
{
  "instruction": "Summarize the configuration process",
  "output": "This guide covers installation and basic setup steps...",
  "category": "summary"
}
```

FAQ:
```json
{
  "instruction": "How do I install?",
  "output": "Download from example.com and run the installer",
  "category": "faq"
}
```

Guide:
```json
{
  "instruction": "Provide installation steps",
  "output": "1. Download from example.com\n2. Run installer\n3. Configure settings",
  "category": "guide"
}
```

## Advanced Usage

### Script: Batch Process Multiple PDFs

```python
import os
from config import ConfigLoader
from scraper import WebScraper
from transformer import ContentTransformer
from dataset_generator import DatasetGenerator

pdf_urls = [
    "https://example.com/doc1.pdf",
    "https://example.com/doc2.pdf",
    "https://example.com/resources/whitepaper",  # Auto-detected
]

# Create config programmatically
config = {
    'sources': [
        {
            'name': f"PDF {i+1}",
            'url': url,
            'scrape_type': 'pdf'
        }
        for i, url in enumerate(pdf_urls)
    ],
    'llm': {
        'provider': 'ollama',
        'model': 'mistral'
    }
}

# Process
scraper = WebScraper(config, 'raw_pdf_content', workers=2)
scraper.scrape_all()

transformer = ContentTransformer(config, workers=4)
transformer.transform_all('raw_pdf_content', 'transformed_pdf')

generator = DatasetGenerator('transformed_pdf', 'pdf_datasets', config)
generator.generate_all(['faq', 'summary'])
```

### Script: Check PDF Extraction Quality

```python
import json
from pathlib import Path

def check_pdf_extraction(content_dir):
    """Verify PDF text extraction quality"""
    for json_file in Path(content_dir).glob('*_pdf.json'):
        with open(json_file) as f:
            data = json.load(f)
        
        content = data['content']
        lines = content.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]
        
        print(f"\n{json_file.name}:")
        print(f"  Total chars: {len(content):,}")
        print(f"  Non-empty lines: {len(non_empty_lines)}")
        print(f"  Avg line length: {len(content) // max(len(lines), 1)}")
        print(f"  First 200 chars: {content[:200]}")

check_pdf_extraction('raw_content')
```

## Troubleshooting

### PDF Not Detected

**Problem**: PDF served as HTML URL not detected

**Debug**:
```bash
# Check what content-type server returns
curl -I https://example.com/document

# Look for "Content-Type: application/pdf"
# or "Content-Type: application/octet-stream"
```

**Solution**:
- Explicitly set `scrape_type: "pdf"`
- Check URL ends with .pdf or similar
- Verify server isn't using custom content-types

### Incomplete Text Extraction

**Problem**: Some pages not extracting text

**Debug**:
```python
import PyPDF2
with open('document.pdf', 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text.strip():
            print(f"Page {i+1} has no text")
```

**Solution**:
- Check page format (scanned vs searchable)
- Use PDF repair/optimization tool
- Pre-process with external tools if needed

### Memory Issues with Large PDFs

**Problem**: System runs out of memory with large PDFs

**Solution**:
```yaml
processing:
  chunk_size: 1000  # Much smaller chunks
  workers: 1        # Single worker to reduce memory
```

or

```python
# Process one PDF at a time
for source in config['sources']:
    if source['scrape_type'] == 'pdf':
        scraper.scrape_source(source)
        del source  # Free memory
```

## See Also

- [Configuration Guide](CONFIG_GUIDE.md)
- [Architecture Guide](ARCHITECTURE.md)
- [README](README.md) - Quick start guide
- [Recursive Crawling](RECURSIVE_CRAWLING.md) - For handling websites with PDF links

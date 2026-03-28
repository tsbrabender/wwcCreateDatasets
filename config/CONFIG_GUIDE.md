# Configuration Guide

This guide provides comprehensive documentation for configuring the LLM Training Data Generator.

## Table of Contents

1. [Basic Configuration](#basic-configuration)
2. [Data Sources](#data-sources)
3. [LLM Providers](#llm-providers)
4. [Environment Variables](#environment-variables)
5. [Advanced Options](#advanced-options)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)

## Basic Configuration

The configuration file uses YAML format. Create a file named `config/config.yaml` in the project directory (or copy from the template in the `config/` folder).

### Minimal Configuration

```yaml
sources:
  - name: "My Website"
    url: "https://example.com"
    scrape_type: "web"

llm:
  provider: "openai"
  model: "gpt-3.5-turbo"
  api_key: "${OPENAI_API_KEY}"
```

## Data Sources

The `sources` section defines where to scrape training data from.

### Web Source

```yaml
sources:
  - name: "Documentation Site"
    url: "https://docs.example.com"
    scrape_type: "web"
    content_selector: "main"  # CSS selector
```

**Parameters:**
- `name` (required): Human-readable name for the source
- `url` (required): Full URL to scrape from
- `scrape_type` (required): Must be "web"
- `content_selector` (optional): CSS selector for content extraction (default: "body")

**CSS Selector Examples:**
```yaml
content_selector: "main"           # <main> tag
content_selector: ".content"       # class="content"
content_selector: "#article"       # id="article"
content_selector: "article p"      # All <p> inside <article>
content_selector: "div.post-body"  # <div> with class post-body
```

### Excluding Repetitive Elements

When scraping multiple pages from the same website, common elements like headers, footers, and navigation appear on every page. This creates redundant training data. Use `exclude_selectors` to remove these elements before saving content.

**Problem:** Scraping 100 pages means your headers/footers appear 100 times in training data, reducing quality.

**Solution:** Specify CSS selectors to exclude:

```yaml
sources:
  - name: "Documentation Site"
    url: "https://docs.example.com"
    scrape_type: "web"
    content_selector: "main"
    exclude_selectors:
      - "header"           # Remove <header> tag
      - "footer"           # Remove <footer> tag
      - "nav"              # Remove <nav> tag
      - ".sidebar"         # Remove elements with class "sidebar"
      - ".breadcrumb"      # Remove breadcrumb navigation
      - ".advertisement"   # Remove ads
      - "[role='banner']"  # Remove ARIA banner elements
    recursive: true
    crawl_depth: 10
```

**How It Works:**
1. Fetches HTML page
2. Removes all elements matching `exclude_selectors` using CSS selector matching
3. Extracts remaining content using `content_selector`
4. Saves cleaned content without repeated headers/footers

**Common Selectors to Exclude:**
```yaml
exclude_selectors:
  - "header"              # Common header tag
  - "footer"              # Common footer tag
  - "nav"                 # Navigation elements
  - ".navbar"             # Bootstrap navbar
  - ".sidebar"            # Sidebar content
  - ".breadcrumb"         # Breadcrumb navigation
  - ".advertisement"      # Ad containers
  - ".social-links"       # Social media links
  - ".related-posts"      # Related content
  - "[role='banner']"     # ARIA banner role
  - "[role='navigation']" # ARIA navigation role
  - ".skip-links"         # Skip navigation links
```

**Benefits:**
- Reduces duplicate content in training data
- Improves training quality by focusing on unique content
- Smaller dataset files
- Better LLM training results

### PDF Source

```yaml
sources:
  - name: "Technical Guide PDF"
    url: "https://example.com/guide.pdf"
    scrape_type: "pdf"
```

**Parameters:**
- `name` (required): Human-readable name
- `url` (required): URL to PDF file
- `scrape_type` (required): Must be "pdf"

**Automatic PDF Detection:**
The system automatically detects PDFs even when served as HTML URLs:
- Checks HTTP Content-Type header for "application/pdf"
- Falls back to checking URL extension (.pdf)
- If detected as PDF, automatically extracts text using PyPDF2
- No need to manually set `scrape_type: "pdf"` for PDF files

### API Source

```yaml
sources:
  - name: "API Data"
    url: "https://api.example.com/v1/documentation"
    scrape_type: "api"
```

**Parameters:**
- `name` (required): Human-readable name
- `url` (required): API endpoint URL
- `scrape_type` (required): Must be "api"

The API response will be saved as JSON. Ensure the endpoint returns valid JSON.

### Adding Multiple Sources

```yaml
sources:
  - name: "Source 1"
    url: "https://example.com/docs"
    scrape_type: "web"
    content_selector: "main"
  
  - name: "Source 2"
    url: "https://guide.example.com/tutorial.pdf"
    scrape_type: "pdf"
  
  - name: "Source 3"
    url: "https://api.example.com/content"
    scrape_type: "api"
```

## LLM Providers

The `llm` section configures the LLM used for content transformation.

### OpenAI

```yaml
llm:
  provider: "openai"
  model: "gpt-3.5-turbo"  # or "gpt-4", "gpt-4-turbo", etc.
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.7
```

**Available Models:**
- `gpt-3.5-turbo` - Fast, affordable (recommended for starting)
- `gpt-4` - More powerful, higher cost
- `gpt-4-turbo` - Faster GPT-4 variant
- `gpt-4o` - Latest optimized model

**Cost Estimate:**
- GPT-3.5-turbo: ~$0.50-$1.00 per 1M tokens
- GPT-4: ~$30-$60 per 1M tokens
- GPT-4-turbo: ~$10-$30 per 1M tokens

### Anthropic Claude

```yaml
llm:
  provider: "anthropic"
  model: "claude-3-sonnet-20240229"  # or "claude-3-opus-20240229"
  api_key: "${ANTHROPIC_API_KEY}"
```

**Available Models:**
- `claude-3-haiku-20240307` - Fast, low-cost
- `claude-3-sonnet-20240229` - Balanced
- `claude-3-opus-20240229` - Most capable

### Ollama (Local/Self-Hosted)

```yaml
llm:
  provider: "ollama"
  model: "llama2"  # or "mistral", "neural-chat", etc.
  host: "http://localhost:11434"
  # api_key: not required
```

**Installation:**
```bash
# Download and install Ollama from https://ollama.ai

# Run Ollama service
ollama serve

# In another terminal, pull a model
ollama pull llama2
ollama pull mistral
ollama pull neural-chat
```

**Available Models:**
- `llama2` - 7B, 13B, 70B variants
- `mistral` - 7B model, fast and capable
- `neural-chat` - Optimized for chat/dialogue
- `dolphin-mixtral` - Creative and detailed responses
- `orca-mini` - Lightweight

**Benefits:**
- No API costs
- Full privacy (data stays local)
- Faster iteration for development
- No rate limits

## Environment Variables

The configuration supports environment variable substitution for sensitive data.

### Using Environment Variables

```yaml
llm:
  api_key: "${OPENAI_API_KEY}"
  # or with default value
  api_key: "${API_KEY_DEFAULT_VALUE}"
```

### Setting Environment Variables

**On Linux/macOS:**
```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

**On Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-..."
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

**On Windows (CMD):**
```cmd
setx OPENAI_API_KEY "sk-..."
setx ANTHROPIC_API_KEY "sk-ant-..."
```

### Best Practices

1. **Never commit API keys** to version control
2. **Use `.gitignore`** to exclude config files with credentials
3. **Use environment variables** instead of hardcoding secrets
4. **Create `.env` file** (optional, not tracked in git):
   ```bash
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=sk-ant-...
   ```

## Advanced Options

### Output Configuration

```yaml
output:
  format: "jsonl"              # Always "jsonl" for UnSloth
  include_metadata: true       # Include source metadata in output
```

### Processing Configuration

```yaml
processing:
  chunk_size: 2000             # Max characters per chunk
  batch_size: 16               # Items processed in parallel
  workers: 2                   # Concurrent scraping workers
```

**Parameters:**
- `chunk_size`: Larger = fewer API calls but may hit token limits. Typical: 1000-3000
- `batch_size`: Larger = faster but uses more memory. Typical: 8-32
- `workers`: More = faster scraping but may hit rate limits. Typical: 2-4

### Generation Parameters

```yaml
llm:
  temperature: 0.7             # 0 = deterministic, 1 = creative (0.0-2.0)
  max_tokens: 1024             # Max tokens per response
  top_p: 0.9                   # Nucleus sampling parameter
```

## Examples

### Example 1: Blog to Training Data

```yaml
# Scrape a blog and generate training data

sources:
  - name: "AI Insights Blog"
    url: "https://blog.example.com/ai"
    scrape_type: "web"
    content_selector: "article.post-content"

llm:
  provider: "openai"
  model: "gpt-3.5-turbo"
  api_key: "${OPENAI_API_KEY}"
  temperature: 0.7
```

### Example 2: Academic Papers (PDF)

```yaml
sources:
  - name: "ML Research Paper 1"
    url: "https://arxiv.org/pdf/2301.12345.pdf"
    scrape_type: "pdf"
  
  - name: "ML Research Paper 2"
    url: "https://arxiv.org/pdf/2302.54321.pdf"
    scrape_type: "pdf"

llm:
  provider: "ollama"
  model: "mistral"
  host: "http://localhost:11434"
```

### Example 3: Mixed Sources

```yaml
sources:
  - name: "Official Documentation"
    url: "https://docs.framework.com"
    scrape_type: "web"
    content_selector: "div.documentation"
  
  - name: "Tutorial PDF"
    url: "https://example.com/tutorial.pdf"
    scrape_type: "pdf"
  
  - name: "API Docs"
    url: "https://api.example.com/v1/documentation"
    scrape_type: "api"

llm:
  provider: "anthropic"
  model: "claude-3-sonnet-20240229"
  api_key: "${ANTHROPIC_API_KEY}"
  temperature: 0.8  # Slightly more creative for explanations
```

### Example 4: Production Setup with Multiple LLMs

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

llm:
  # Switch providers by changing this line
  # For development: ollama
  # For production: openai or anthropic
  
  # Option 1: Development with Ollama (free)
  provider: "ollama"
  model: "mistral"
  
  # Option 2: Production with OpenAI (paid)
  # provider: "openai"
  # model: "gpt-4"
  # api_key: "${OPENAI_API_KEY}"
```

## Troubleshooting

### Configuration Validation Error

**Problem:** `ValidationError: Configuration missing required field`

**Solution:**
- Check all required fields are present: `sources` and `llm`
- Verify YAML indentation (2 spaces, not tabs)
- Use a YAML validator: `python -c "import yaml; yaml.safe_load(open('config.yaml'))"`

### URL Not Accessible

**Problem:** `ScraperError: Failed to fetch https://...`

**Solutions:**
1. Check URL is correct and accessible
2. Add a proxy if needed:
   ```bash
   export HTTP_PROXY=http://proxy.company.com:8080
   ```
3. Increase timeout: modify `DEFAULT_TIMEOUT` in `scraper.py`

### CSS Selector Not Finding Content

**Problem:** `Warning: Content selector '...' not found`

**Solution:**
1. Inspect the website with browser DevTools (F12)
2. Find the correct CSS selector for main content
3. Test selector using browser console:
   ```javascript
   document.querySelectorAll('your-selector')
   ```

### API Key Errors

**Problem:** `AuthenticationError: Invalid API key`

**Solutions:**
1. Verify API key is correct
2. Check key hasn't expired or been revoked
3. Verify environment variable is set:
   ```bash
   echo $OPENAI_API_KEY
   ```

### Out of Memory

**Problem:** Process killed or memory error

**Solutions:**
1. Reduce batch size: `--batch-size 8`
2. Reduce workers: `--workers 1`
3. Use smaller chunk size in config
4. Process data in smaller batches

### Rate Limit Errors

**Problem:** `RateLimitError` from API provider

**Solutions:**
1. Reduce workers: `--workers 1`
2. Add delays between requests (modify `scraper.py`)
3. Use cheaper model option
4. Switch to Ollama for local processing

## Next Steps

1. Create your `config.yaml` file based on your needs
2. Set up API keys for your chosen LLM provider
3. Run: `python main.py --config config.yaml`
4. Check output in `datasets/` directory
5. Review `DATASET_SUMMARY.md` for statistics

For more information:
- See [README.md](README.md) for usage examples
- See [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- See [RATIONALE.md](RATIONALE.md) for design decisions

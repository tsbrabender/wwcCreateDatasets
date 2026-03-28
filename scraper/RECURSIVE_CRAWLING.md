# Recursive Website Crawling Guide

## Overview

The LLM Training Data Generator now supports **recursive website crawling**, allowing you to automatically extract content from entire websites up to a configurable depth level. This enables you to create comprehensive training datasets from complete documentation sites, blogs, and other web properties.

## Key Features

- **Automatic Link Following**: Discovers and crawls all links on a website
- **Same-Domain Filtering**: Prevents crawling external sites or ads
- **Automatic PDF Detection**: Detects PDFs served as HTML URLs and automatically extracts text
- **Configurable Depth**: Control how many levels deep to crawl (default: 3)
- **URL Deduplication**: Avoids processing the same page twice
- **Rate Limiting**: Respects target servers with configurable delays between requests
- **Unique File Output**: Each crawled page gets a unique filename using URL hashing
- **Backward Compatible**: Single-page scraping mode still available

## How It Works

### Basic Recursive Crawling

```yaml
sources:
  - name: "Full Documentation"
    url: "https://docs.example.com"
    scrape_type: "web"
    content_selector: "main"
    recursive: true          # Enable recursive crawling
    crawl_depth: 3          # How many levels to crawl
```

When enabled, the scraper will:

1. **Start** at the root URL
2. **Extract** content from the page using the CSS selector
3. **Find** all internal links on the page
4. **Follow** each new link (up to the depth limit)
5. **Repeat** for each discovered page
6. **Skip** external domains and previously visited URLs

### Crawl Depth Explained

The `crawl_depth` parameter controls how many levels of pages are crawled:

- **Depth 1**: Only the root page (`https://docs.example.com`)
- **Depth 2**: Root page + all pages directly linked from root
- **Depth 3**: Root + pages from level 2 + pages linked from level-2 pages
- **Depth 4+**: Even deeper nesting (beware: exponential page count growth)

**Typical Depth Values:**
- `depth: 1` - Single page, no link following
- `depth: 2` - Top-level navigation pages
- `depth: 3` - Most documentation sites (recommended)
- `depth: 4` - Large documentation with deep nesting
- `depth: 5+` - Very large sites (can take a long time)

### Example: Documentation Site Structure

```
https://docs.example.com/
├── /getting-started       (depth 1 link)
│   ├── /installation      (depth 2 link)
│   └── /setup            (depth 2 link)
├── /api
│   ├── /reference        (depth 2 link)
│   └── /examples         (depth 2 link)
└── /tutorials
    ├── /basic            (depth 2 link)
    └── /advanced         (depth 2 link)
```

With `crawl_depth: 2`, the crawler would get: root + 6 subsections = 7 pages total.

### Page Limiting with max_pages

The `max_pages` parameter provides an alternative or complement to `crawl_depth` for controlling crawl scope:

- **`crawl_depth`**: Limits how many *levels* deep to traverse (structural limit)
- **`max_pages`**: Limits the *total number* of pages retrieved (count limit)

**When to use each:**
- Use **`crawl_depth`** when you want to ensure you explore all pages at certain tree levels
- Use **`max_pages`** when you want a fixed limit on total content volume
- Use **both** together for fine-grained control (crawl stops when either limit is reached)

**Example: Controlling Large Sites**

```yaml
sources:
  - name: "Large Documentation"
    url: "https://massive-docs.example.com"
    scrape_type: "web"
    recursive: true
    crawl_depth: 5          # Explore up to 5 levels deep
    max_pages: 500          # But stop if we reach 500 total pages
```

Without `max_pages`, this could crawl thousands of pages. With both parameters, it respects the first limit reached.

**max_pages Values:**
- `"max"` - Unlimited pages (default)
- `-1` - Unlimited pages (alternative)
- `None` - Unlimited pages (programmatic default)
- `100` - Limit to exactly 100 pages per source

## Configuration Options

### Source-Level Parameters

```yaml
sources:
  - name: "My Website"
    url: "https://example.com"
    scrape_type: "web"
    content_selector: "main"
    
    # Recursive crawling options
    recursive: true          # Enable/disable recursive crawling (default: true)
    crawl_depth: 3          # How many levels deep (default: global default)
    max_pages: 100          # Max pages to crawl (override global setting, "max"/-1/None = unlimited)
```

### Global Processing Parameters

```yaml
processing:
  workers: 2               # Concurrent scraping workers
  chunk_size: 2000        # LLM processing chunk size
  batch_size: 16          # LLM batch processing size
  
  # Recursive crawl defaults (apply to all sources)
  crawl_depth: 3         # Default depth for recursive sources
  crawl_delay: 0.5       # Delay between requests (seconds)
  max_pages: "max"       # Max pages per source ("max"/-1/None = unlimited, or specify number like 100)
```

## Configuration Examples

### Example 1: Single Page (No Recursion)

```yaml
sources:
  - name: "Specific Page"
    url: "https://blog.example.com/article-123"
    scrape_type: "web"
    content_selector: "article"
    recursive: false       # Don't follow links
```

**Output**: One JSON file with content from the single page.

### Example 2: Full Documentation Site (Recommended)

```yaml
sources:
  - name: "Python Documentation"
    url: "https://docs.python.org"
    scrape_type: "web"
    content_selector: "main"
    recursive: true
    crawl_depth: 3
```

**Output**: Multiple JSON files (one per crawled page), e.g.:
- `python_documentation_web_abc12345.json` (root page)
- `python_documentation_web_def67890.json` (page 2)
- `python_documentation_web_ghi24680.json` (page 3)
- etc.

### Example 3: Deep Crawl for Large Sites

```yaml
sources:
  - name: "Framework Docs"
    url: "https://docs.framework.io"
    scrape_type: "web"
    content_selector: ".documentation-content"
    recursive: true
    crawl_depth: 4        # Deeper crawl for comprehensive coverage
```

### Example 4: Multiple Sites with Different Depths

```yaml
sources:
  # Small documentation
  - name: "Library API"
    url: "https://api.example.com"
    scrape_type: "web"
    content_selector: "main"
    recursive: true
    crawl_depth: 2        # Shallow crawl
  
  # Large documentation
  - name: "Enterprise Docs"
    url: "https://docs.enterprise.com"
    scrape_type: "web"
    content_selector: ".main-content"
    recursive: true
    crawl_depth: 4        # Deeper crawl

# Global defaults apply when not specified per-source
processing:
  crawl_depth: 3
  crawl_delay: 0.5
```

### Example 5: Page Limiting with max_pages

```yaml
sources:
  # Controlled website crawl
  - name: "Documentation with Limit"
    url: "https://docs.example.com"
    scrape_type: "web"
    content_selector: "main"
    recursive: true
    crawl_depth: 5
    max_pages: 100        # Per-source override: stop at 100 pages
  
  # Global limit with per-source override
  - name: "Large API Docs"
    url: "https://api.example.com/docs"
    scrape_type: "web"
    recursive: true
    max_pages: 50         # More restrictive override

# Global settings
processing:
  crawl_depth: 3
  max_pages: "max"        # Default: unlimited for all sources
  crawl_delay: 0.5
```

In this example:
- First source stops at 100 pages (whichever comes first: depth=5 or pages=100)
- Second source stops at 50 pages (overrides global "max")
- Both sources respect the global crawl_delay

## Output Files

### File Naming

For recursive crawling, output files include a URL hash to ensure uniqueness:

```
source_name_web_XXXXXXXX.json
```

Example outputs from crawling `https://docs.example.com`:

```
example_documentation_web.json           # Root page
example_documentation_web_a1b2c3d4.json  # /page1
example_documentation_web_e5f6g7h8.json  # /page2
example_documentation_web_i9j0k1l2.json  # /page3
...
```

### File Contents

Each JSON file contains:

```json
{
  "metadata": {
    "name": "Example Documentation",
    "url": "https://docs.example.com/page",
    "scrape_type": "web",
    "scraped_at": "2024-01-15 14:30:45",
    "content_length": 15234
  },
  "content": "Your page content here..."
}
```

## Performance Considerations

### Page Count Estimation

The number of pages crawled grows with depth:

- **Shallow structure** (avg 5 links per page):
  - Depth 1: 1 page
  - Depth 2: 6 pages
  - Depth 3: 31 pages
  - Depth 4: 156 pages

- **Dense structure** (avg 20 links per page):
  - Depth 1: 1 page
  - Depth 2: 21 pages
  - Depth 3: 421 pages
  - Depth 4: 8,421 pages

### Time Estimates

With default settings (0.5 sec delay between requests, 2 workers):

- **Depth 2**: ~10 seconds to 1 minute
- **Depth 3**: ~1-5 minutes
- **Depth 4**: ~5-30 minutes
- **Depth 5**: Can take 30+ minutes

### Optimization Tips

1. **Reduce `crawl_delay`** for faster crawling (be respectful to servers):
   ```yaml
   processing:
     crawl_delay: 0.2  # 200ms instead of 500ms
   ```

2. **Increase `workers`** for parallel scraping:
   ```yaml
   processing:
     workers: 4  # Use more parallel workers
   ```

3. **Reduce `crawl_depth`** if possible:
   ```yaml
   crawl_depth: 2  # Crawl fewer levels
   ```

4. **Use more specific CSS selectors** to avoid processing unnecessary content:
   ```yaml
   content_selector: "article.main-content"  # More specific
   ```

## Rate Limiting and Server Respect

### Default Behavior

- **Rate Limit**: 0.5 seconds between requests (configurable)
- **User-Agent**: Standard identifying the application
- **Same-Domain Only**: No external site crawling

### Best Practices

1. **Check robots.txt**: Ensure the site allows crawling
2. **Adjust crawl_delay** appropriately:
   - Small, fast servers: 0.2-0.5 seconds
   - Medium servers: 0.5-1 second
   - Large CDN-backed sites: 1+ seconds

3. **Monitor for blocking**:
   - If you see 403 or 429 errors, increase `crawl_delay`
   - Reduce `workers` to lower concurrent requests

### Respecting Site Terms

- Review the site's `robots.txt` at `https://example.com/robots.txt`
- Check Terms of Service for scraping permissions
- Consider alternative data sources (APIs, official datasets)
- Use for training purposes only, not for republishing

## Troubleshooting

### Issue: Getting 403 or 429 Errors

**Problem**: Server is blocking or rate-limiting requests

**Solutions**:
1. Increase `crawl_delay`:
   ```yaml
   processing:
     crawl_delay: 2.0  # 2 seconds between requests
   ```

2. Reduce `workers`:
   ```yaml
   processing:
     workers: 1  # Use single worker
   ```

3. Check if site allows scraping in `robots.txt`

### Issue: No Content Being Extracted

**Problem**: CSS selector not matching page structure

**Solutions**:
1. Inspect the page with browser Developer Tools (F12)
2. Test the selector in browser console:
   ```javascript
   document.querySelectorAll('your-selector')
   ```
3. Adjust selector in config
4. Try more general selector (e.g., `"body"` or `"main"`)

### Issue: Crawling Takes Too Long

**Problem**: Too many pages or excessive depth

**Solutions**:
1. Reduce `crawl_depth`:
   ```yaml
   crawl_depth: 2  # Shallower crawl
   ```

2. Increase `workers` and reduce `crawl_delay`:
   ```yaml
   processing:
     workers: 4         # More parallel
     crawl_delay: 0.1  # Shorter delay
   ```

3. Check page size - use smaller `chunk_size` for processing:
   ```yaml
   processing:
     chunk_size: 1000  # Smaller chunks
   ```

### Issue: Getting Duplicate Content

**Problem**: Same content being processed multiple times

**Solutions**:
- This should not happen; URL deduplication is automatic
- Check for URL variations (www vs non-www, trailing slashes)
- Review output files for actual duplicates

## Advanced Usage

### Combining Recursive Crawling with transformations

```python
from main import setup_logging
from config import ConfigLoader
from scraper import WebScraper
from transformer import ContentTransformer
from dataset_generator import DatasetGenerator
from jsonl_exporter import JSONLExporter

# Load config with recursive crawling
config = ConfigLoader('config.yaml').load()

# Scrape entire website recursively
scraper = WebScraper(config, output_dir='raw_content', workers=4)
scraper.scrape_all()

# Transform all crawled content
transformer = ContentTransformer(config, workers=2)
transformer.transform_all('raw_content', 'transformed_content')

# Generate datasets
generator = DatasetGenerator('transformed_content', 'datasets', config)
generator.generate_all(['instruction_response', 'faq'])

# Export to JSONL
exporter = JSONLExporter()
exporter.export_all('datasets', 'final_datasets', config)
```

### Script: Get Crawl Statistics

```python
import json
from pathlib import Path

def get_crawl_stats(content_dir):
    content_path = Path(content_dir)
    files = list(content_path.glob('*.json'))
    
    total_content = 0
    unique_domains = set()
    
    for file in files:
        with open(file) as f:
            data = json.load(f)
            total_content += data['metadata']['content_length']
            # Extract domain from URL
            url = data['metadata']['url']
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            unique_domains.add(domain)
    
    print(f"Files crawled: {len(files)}")
    print(f"Total content: {total_content:,} characters")
    print(f"Average per page: {total_content // len(files) if files else 0:,} characters")
    print(f"Unique domains: {len(unique_domains)}")
    
    return {
        'files': len(files),
        'total_content': total_content,
        'unique_domains': len(unique_domains)
    }

# Usage
stats = get_crawl_stats('raw_content')
```

## FAQ

**Q: Will recursive crawling follow links outside my site?**
A: No. Recursive crawling is domain-specific and filters external links automatically. It handles `www.` variations correctly.

**Q: Can I crawl multiple sites?**
A: Yes, add multiple source entries in your `config.yaml`. Each can have its own `recursive` and `crawl_depth` settings.

**Q: What if a page takes a long time to load?**
A: Requests have a 30-second timeout by default. If pages are timing out, check network speed or reduce `crawl_depth`.

**Q: Can I resume a interrupted crawl?**
A: Currently, no. Crawls restart from the beginning. Plan accordingly for large sites.

**Q: How do I know how many pages will be crawled?**
A: You can't know exactly without crawling, but estimate based on site structure and use shallow `crawl_depth` first.

**Q: Should I crawl at depth 5+ for comprehensive data?**
A: Usually not. Depth 3-4 captures most documentation. Deeper levels may include low-value pages (archives, tags, etc.).

## See Also

- [Configuration Guide](CONFIG_GUIDE.md)
- [Architecture Guide](ARCHITECTURE.md)
- [README](README.md) - Quick start guide

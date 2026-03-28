# Developer Guide - Maintaining Project Structure

## Overview

This guide helps developers maintain and extend the modular project structure.

## Package Guidelines

### When to Create a New Package

Create a new package when you have:
- A set of related, focused functionality
- Public APIs that other packages should use
- Specific documentation or configuration

**Do NOT create a package for:**
- Single utility functions (add to `utils_module/`)
- Internal helper code (keep in same package)
- Temporary/experimental code (use a branch instead)

### Package Structure Template

```
my_feature/
├── __init__.py              # Public API exports
├── main_module.py           # Core implementation
├── helpers.py               # Internal helpers (optional)
├── MY_FEATURE_GUIDE.md     # Detailed docs (if needed)
└── tests/                  # Unit tests (optional)
    └── test_main_module.py
```

### Sample `__init__.py`

```python
"""My Feature Package

Short description of what this package does.
"""

from .main_module import MyClass, my_function

__all__ = ['MyClass', 'my_function']
```

## Import Conventions

### Root-to-Package Imports

Always use package-relative imports:

```python
# ✅ Good - Import from package
from scraper import WebScraper
from transform import ContentTransformer

# ❌ Avoid - Importing from parent
from ..scraper import WebScraper  # Don't use relative imports from root
```

### Within Packages

Use regular imports (absolute preferred):

```python
# ✅ In transform/__init__.py
from .transformer import ContentTransformer

# ✅ In scraper/scraper.py for utilities
from config import ConfigLoader
from utils_module import setup_logging
```

### Cross-Package Dependencies

Keep minimal. Prefer passing data rather than tight coupling:

```python
# ✅ Good - Clean interface
config = ConfigLoader('config/config.yaml').load()
scraper = WebScraper(config, output_dir)

# ❌ Avoid - Tight coupling
scraper = WebScraper()
scraper.use_config(config_module.global_config)
```

## Adding a New LLM Provider

**Goal**: Add support for a new LLM (e.g., Google's Vertex AI)

### Steps

1. **Update `transform/transformer.py`**:

```python
class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    GOOGLE_VERTEX = "google-vertex"  # Add new provider


class ContentTransformer:
    def _initialize_llm_client(self) -> None:
        provider = self.llm_config.get('provider', 'openai').lower()
        
        # ... existing code ...
        
        elif provider == 'google-vertex':  # Add new branch
            import vertexai
            vertexai.init(project=self.llm_config.get('project_id'))
            self.client = vertexai.language_models.TextGenerationModel
```

2. **Update `config/config.template.yaml`**:

```yaml
llm:
  provider: google-vertex  # Add example
  project_id: "my-gcp-project"
  model: "text-bison"
  temperature: 0.7
```

3. **Update `config/CONFIG_GUIDE.md`**:

Document the new provider and its configuration options.

4. **Update `transform/transformer.py _call_llm()` method**:

Add provider-specific logic.

5. **Test**:

```python
# examples/examples.py or new test
from transform import ContentTransformer

transformer = ContentTransformer(
    llm_config={
        'provider': 'google-vertex',
        'project_id': 'my-project',
        'model': 'text-bison'
    },
    input_dir=Path('./raw'),
    output_dir=Path('./transformed')
)
transformer.transform_all()
```

## Adding a New Dataset Type

**Goal**: Add "code-comments" dataset (source code with AI-generated comments)

### Steps

1. **Update `generate/dataset_generator.py`**:

```python
@dataclass
class CodeCommentsPair:
    """Code snippet with AI-generated comments."""
    code: str
    comments: str
    language: str = "python"
    category: str = "code-comments"


class DatasetGenerator:
    def generate_code_comments(self) -> None:
        """Generate code-with-comments dataset."""
        items = []
        
        for content_file in self.transformed_dir.glob('transformed_*.json'):
            with open(content_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract code snippets and generate comments
            # Implementation details...
        
        self._save_dataset('code_comments', items)
```

2. **Update `main.py`**:

```python
if dataset_type in ['all', 'code-comments']:
    generator.generate_code_comments()
```

3. **Update CLI help**:

Update `main.py` argparse choices for `--dataset-type` to include 'code-comments'.

4. **Document**: Add to `docs/DATASET_TYPES.md` or `generate/README.md`

## Adding a New Scraper Type

**Goal**: Add Email list scraping

### Steps

1. **Create `scraper/email_scraper.py`** (or extend existing):

```python
def _scrape_email_list(self, source: Dict[str, Any]) -> None:
    """Scrape email list from plain text endpoint."""
    url = source['url']
    emails = self._fetch_email_list(url)
    self._save_source_content(source, '\n'.join(emails), 'email-list')
```

2. **Update `scraper/__init__.py`**:

Export new functionality.

3. **Update `config/config.template.yaml`**:

```yaml
sources:
  - name: "Email List"
    url: "https://example.com/emails"
    scrape_type: "email-list"
```

4. **Handle in `scraper/scraper.py scrape_source()`**:

```python
elif source_type == 'email-list':
    self._scrape_email_list(source)
```

## Code Style Guidelines

### Naming

- **Classes**: PascalCase (`WebScraper`, `ContentTransformer`)
- **Functions**: snake_case (`transform_all()`, `extract_links()`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_TIMEOUT = 15`)
- **Private methods**: prefix with underscore (`_extract_links()`)

### Documentation

Every public class/function needs:

```python
def process_items(items: List[str], config: Dict[str, Any]) -> Optional[Dict]:
    """
    Brief one-line description.
    
    Longer explanation if needed. Can span multiple lines.
    Include key details about behavior.
    
    Args:
        items: Description of items parameter
        config: Description of config parameter
        
    Returns:
        Dict with results or None if failed
        
    Raises:
        ValueError: If validation fails
    """
```

### Type Hints

Use type hints on public APIs:

```python
# ✅ Good
def scrape_source(self, source: Dict[str, Any]) -> None:
    ...

# ❌ Avoid for public APIs
def scrape_source(self, source):
    ...
```

## Error Handling

### Packaging Errors

```python
# ❌ Avoid
import transformer  # Vague

# ✅ Good
from transform import ContentTransformer
```

### Internal vs Public Errors

```python
class TransformerError(Exception):
    """Public error - document in __init__.py"""
    pass

class _ChunkingError(Exception):
    """Internal error - private, not exported"""
    pass
```

## Testing Structure

```
package/
├── __init__.py
├── module.py
└── tests/
    ├── __init__.py
    ├── test_module.py
    └── fixtures/
        ├── sample_input.json
        └── expected_output.json
```

**Run tests**:
```bash
python -m pytest tests/
```

## Common Refactoring Patterns

### Moving Code Between Packages

1. Cut code from source
2. Paste into destination's module
3. Update `__init__.py` exports in destination
4. Update imports in all files that use it
5. Run tests

### Extracting a Helper Function

```python
# ❌ Before - duplicate code in multiple packages
def validate_content(content):
    # validation logic
    return content

# ✅ After - centralize in utils_module
# utils_module/utils.py
def validate_content(content):
    # validation logic
    return content

# Other packages use:
from utils_module import validate_content
```

## Performance Considerations

### Lazy Imports

For heavy dependencies, consider lazy imports in `__init__.py`:

```python
def __getattr__(name):
    if name == 'HeavyClass':
        from .heavy_module import HeavyClass
        return HeavyClass
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
```

### Circular Dependencies

If you have circular imports, restructure:

```
# ❌ Circular
A imports from B
B imports from A

# ✅ Solution
Create C with shared interfaces
A imports from C
B imports from C
```

## Updating Documentation

When you change a package:

1. **Update docstrings** in the code
2. **Update `__init__.py` docstrings** if API changes
3. **Update package-specific README** (if exists)
4. **Update `docs/PROJECT_STRUCTURE.md`** if structure changes
5. **Update examples** if API changes

## Validation Checklist

Before committing changes:

```
□ All imports work (python -m main)
□ No circular dependencies
□ __init__.py exports public API
□ Docstrings current
□ Tests pass (if applicable)
□ Documentation updated
□ No duplicate code left in root
□ Package names are descriptive
```

## Questions?

Refer to:
- `docs/PROJECT_STRUCTURE.md` - Overall layout
- Package-specific `__init__.py` - What's exported
- `examples/examples.py` - Usage examples
- `config/CONFIG_GUIDE.md` - Configuration options

---

Happy coding! Remember: **Keep packages focused, imports clean, and documentation current.** 🎉

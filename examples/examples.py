"""
Example: Using the LLM Training Data Generator as a Library

This file demonstrates how to use the pipeline modules programmatically
instead of just through the CLI. Useful for integration into larger systems.
"""

from pathlib import Path
from config import ConfigLoader
from scraper import WebScraper
from transform import ContentTransformer
from generate import DatasetGenerator
from export import JSONLExporter

# Example 1: Basic Usage - Run Full Pipeline Programmatically
# ============================================================

def example_full_pipeline():
    """Run the complete pipeline using module APIs."""
    
    # Load configuration
    config_loader = ConfigLoader('config/config.yaml')
    config = config_loader.load()
    
    # Set up directories
    output_dir = Path('./datasets')
    raw_content_dir = output_dir / 'raw_content'
    transformed_dir = output_dir / 'transformed'
    raw_content_dir.mkdir(parents=True, exist_ok=True)
    transformed_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Scrape content
    scraper = WebScraper(
        config=config,
        output_dir=raw_content_dir,
        workers=2
    )
    scraper.scrape_all()
    
    # Step 2: Transform with LLM
    transformer = ContentTransformer(
        llm_config=config.get('llm', {}),
        input_dir=raw_content_dir,
        output_dir=transformed_dir,
        batch_size=16
    )
    transformer.transform_all()
    
    # Step 3: Generate datasets
    dataset_generator = DatasetGenerator(
        transformed_dir=transformed_dir,
        config=config
    )
    dataset_generator.generate_instruction_response()
    dataset_generator.generate_summary()
    dataset_generator.generate_faq()
    dataset_generator.generate_guide()
    dataset_generator.generate_explanation()
    dataset_generator.generate_multi_turn()
    
    # Step 4: Export to JSONL
    exporter = JSONLExporter(
        dataset_dir=output_dir / 'datasets',
        output_dir=output_dir
    )
    exporter.export_all()


# Example 2: Custom Scraping Only
# ================================

def example_scraping_only():
    """Use just the scraper without full pipeline."""
    
    from config import ConfigLoader
    from scraper import WebScraper
    
    config_loader = ConfigLoader('config/config.yaml')
    config = config_loader.load()
    
    scraper = WebScraper(
        config=config,
        output_dir=Path('./raw_data'),
        workers=3
    )
    
    # Scrape a specific source
    source = config['sources'][0]
    scraper.scrape_source(source)
    
    print(f"Content saved to: ./raw_data")


# Example 3: Custom Transformation
# =================================

def example_transformation_with_custom_chunks():
    """Transform content with custom settings."""
    
    from transform import ContentTransformer
    
    transformer = ContentTransformer(
        llm_config={
            'provider': 'openai',
            'model': 'gpt-3.5-turbo',
            'temperature': 0.5
        },
        input_dir=Path('./raw_content'),
        output_dir=Path('./transformed'),
        batch_size=8  # Smaller batches
    )
    
    transformer.transform_all()


# Example 4: Generate Only Specific Datasets
# ===========================================

def example_specific_datasets():
    """Generate only FAQ and multi-turn datasets."""
    
    from generate import DatasetGenerator
    
    generator = DatasetGenerator(
        transformed_dir=Path('./transformed'),
        config={}
    )
    
    # Generate only FAQs
    generator.generate_faq()
    
    # Generate only multi-turn dialogues
    generator.generate_multi_turn()
    
    print("Generated FAQ and multi-turn datasets")


# Example 5: Export with Custom Validation
# =========================================

def example_validation_and_export():
    """Export datasets with validation."""
    
    from export import JSONLExporter
    import json
    
    exporter = JSONLExporter(
        dataset_dir=Path('./datasets'),
        output_dir=Path('./final_output')
    )
    
    # Export all datasets
    exporter.export_all()
    
    # Custom validation of exported files
    export_file = Path('./final_output/final_instruction_response.jsonl')
    
    if export_file.exists():
        with open(export_file, 'r') as f:
            items = [json.loads(line) for line in f if line.strip()]
            print(f"Exported {len(items)} instruction-response pairs")
            
            # Check data quality
            required_fields = {'instruction', 'output'}
            for i, item in enumerate(items[:5]):  # Check first 5
                if required_fields.issubset(item.keys()):
                    print(f"  ✓ Item {i}: valid")
                else:
                    print(f"  ✗ Item {i}: missing fields")


# Example 6: Streaming Large Datasets
# ====================================

def example_process_large_jsonl_streaming():
    """Process large JSONL files without loading into memory."""
    
    from pathlib import Path
    import json
    
    dataset_file = Path('./datasets/combined_training_data.jsonl')
    
    if dataset_file.exists():
        # Process line by line (memory efficient)
        instruction_count = 0
        question_words = 0
        
        with open(dataset_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue
                
                try:
                    item = json.loads(line)
                    
                    if item.get('instruction'):
                        instruction_count += 1
                        
                        # Count items starting with question words
                        instruction = item['instruction'].lower()
                        if any(instruction.startswith(q) for q in ['what', 'why', 'how', 'when']):
                            question_words += 1
                
                except json.JSONDecodeError:
                    continue
        
        print(f"Dataset Statistics:")
        print(f"  Total Instructions: {instruction_count}")
        print(f"  Questions (what/why/how/when): {question_words}")
        print(f"  Percentage: {question_words/instruction_count*100:.1f}%")


# Example 7: Integration with Hugging Face Datasets
# ==================================================

def example_huggingface_integration():
    """Load generated JSONL with Hugging Face Datasets."""
    
    try:
        from datasets import load_dataset
    except ImportError:
        print("Install hugging-face datasets: pip install datasets")
        return
    
    # Load generated dataset
    dataset = load_dataset(
        'json',
        data_files='datasets/combined_training_data.jsonl'
    )
    
    print(f"Loaded dataset with {len(dataset['train'])} items")
    
    # Show sample
    sample = dataset['train'][0]
    print(f"\nSample item:")
    print(f"  Instruction: {sample['instruction'][:50]}...")
    print(f"  Output: {sample['output'][:50]}...")


# Example 8: Custom Content Processing
# =====================================

def example_custom_content_processing():
    """Process raw content without using LLM (useful for testing)."""
    
    import json
    from pathlib import Path
    
    # Read raw content
    raw_file = Path('./raw_content/sample_web.json')
    
    if raw_file.exists():
        with open(raw_file, 'r') as f:
            data = json.load(f)
        
        content = data['content']
        
        # Simple processing: extract first sentence as instruction
        sentences = content.split('.')
        if sentences:
            summary = sentences[0].strip()
            
            # Create instruction-response pair manually
            pair = {
                'instruction': f"Summarize: {summary}",
                'output': summary,
                'category': 'custom'
            }
            
            print(f"Created pair: {pair}")


# Example 9: Batch Processing with Error Handling
# ===============================================

def example_batch_processing_safe():
    """Process with comprehensive error handling."""
    
    from config import ConfigLoader, ValidationError
    from scraper import WebScraper, ScraperError
    import logging
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Load config with validation
        config_loader = ConfigLoader('config/config.yaml')
        config = config_loader.load()
        print("✓ Configuration loaded and validated")
    
    except ValidationError as e:
        print(f"✗ Configuration error: {e}")
        return
    except FileNotFoundError as e:
        print(f"✗ File not found: {e}")
        return
    
    try:
        # Scrape with error handling
        scraper = WebScraper(config, Path('./raw_content'))
        scraper.scrape_all()
        print("✓ Scraping completed (check logs for any errors)")
    
    except ScraperError as e:
        print(f"✗ Scraping error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


# Main - Choose which example to run
# ==================================

if __name__ == '__main__':
    print("LLM Training Data Generator - Library Usage Examples\n")
    
    # Uncomment which example to run:
    
    # example_full_pipeline()
    # example_scraping_only()
    # example_transformation_with_custom_chunks()
    # example_specific_datasets()
    # example_validation_and_export()
    # example_process_large_jsonl_streaming()
    # example_huggingface_integration()
    # example_custom_content_processing()
    # example_batch_processing_safe()
    
    print("\nTo run an example, uncomment it in the 'if __name__' section")
    print("Or integrate the code into your application as needed")
    
    print("\nFor CLI usage, run: python main.py --config config/config.yaml")

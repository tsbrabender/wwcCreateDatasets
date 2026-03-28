#!/usr/bin/env python3
"""
LLM Training Data Generator - Main CLI Entry Point

This module serves as the command-line interface for the LLM training data pipeline.
It orchestrates the entire workflow: configuration loading, web scraping, content
transformation, and dataset generation.

Usage:
    python main.py --config config/config.yaml --output ./datasets
    python main.py --config config/config.yaml --dataset-type instruction-response
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List

from config import ConfigLoader, ValidationError
from scraper import WebScraper
from transform import ContentTransformer
from generate import DatasetGenerator
from export import JSONLExporter
from utils_module import setup_logging, validate_environment


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed command-line arguments
    """
    parser = argparse.ArgumentParser(
        description="Generate LLM training datasets from web sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config config.yaml --output ./datasets
  %(prog)s --config config.yaml --dataset-type instruction-response
  %(prog)s --config config.yaml --workers 4 --batch-size 32
        """
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='./datasets',
        help='Output directory for generated JSONL files (default: ./datasets)'
    )
    
    parser.add_argument(
        '--dataset-type',
        type=str,
        choices=['all', 'instruction-response', 'summary', 'faq', 
                'guide', 'explanation', 'multi-turn'],
        default='all',
        help='Type of dataset to generate (default: all)'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=2,
        help='Number of concurrent workers for scraping (default: 2)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=16,
        help='Batch size for LLM processing (default: 16)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--skip-scrape',
        action='store_true',
        help='Skip web scraping, use existing content files'
    )
    
    parser.add_argument(
        '--skip-transform',
        action='store_true',
        help='Skip LLM transformation, use existing raw content'
    )
    
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> bool:
    """
    Validate command-line arguments for correctness and consistency.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        bool: True if validation passes, False otherwise
    """
    config_path = Path(args.config)
    if not config_path.exists():
        logging.error(f"Configuration file not found: {config_path}")
        return False
    
    output_path = Path(args.output)
    try:
        output_path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logging.error(f"Cannot create output directory: {e}")
        return False
    
    return True


def setup_pipeline(log_level: str) -> logging.Logger:
    """
    Setup logging and validate environment dependencies.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        logging.Logger: Configured logger instance
        
    Raises:
        RuntimeError: If environment validation fails
    """
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 70)
    logger.info("LLM Training Data Generator - Pipeline Start")
    logger.info("=" * 70)
    
    logger.info("Validating environment and dependencies...")
    validate_environment()
    
    return logger


def load_configuration(config_path: str) -> Dict[str, Any]:
    """
    Load and parse configuration file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Dict[str, Any]: Loaded configuration dictionary
        
    Raises:
        ValidationError: If configuration is invalid
    """
    logger = logging.getLogger(__name__)
    
    logger.info(f"Loading configuration from: {config_path}")
    config_loader = ConfigLoader(config_path)
    config = config_loader.load()
    logger.info(f"Loaded configuration with {len(config.get('sources', []))} sources")
    
    return config


def create_directories(output_dir: str) -> tuple[Path, Path, Path]:
    """
    Create and setup output directories.
    
    Args:
        output_dir: Base output directory path
        
    Returns:
        tuple[Path, Path, Path]: (output_dir, raw_content_dir, transformed_dir)
    """
    logger = logging.getLogger(__name__)
    
    output_path = Path(output_dir)
    raw_content_path = output_path / 'raw_content'
    transformed_path = output_path / 'transformed'
    
    raw_content_path.mkdir(parents=True, exist_ok=True)
    transformed_path.mkdir(parents=True, exist_ok=True)
    
    logger.debug(f"Created output directories at: {output_path}")
    
    return output_path, raw_content_path, transformed_path


def run_scraping_step(
    config: Dict[str, Any],
    output_dir: Path,
    workers: int,
    skip_scrape: bool
) -> None:
    """
    Execute web scraping step.
    
    Args:
        config: Configuration dictionary
        output_dir: Output directory for raw content
        workers: Number of concurrent workers
        skip_scrape: If True, skip this step
    """
    logger = logging.getLogger(__name__)
    
    if skip_scrape:
        logger.info("Step 1: Skipping web scraping")
        return
    
    logger.info("Step 1: Starting web scraping...")
    
    # Extract optional crawl parameters from config
    processing_config = config.get('processing', {})
    scraper_kwargs = {
        'config': config,
        'output_dir': output_dir,
        'workers': workers
    }
    
    # Add optional parameters if specified
    if 'crawl_depth' in processing_config:
        scraper_kwargs['crawl_depth'] = processing_config['crawl_depth']
    if 'crawl_delay' in processing_config:
        scraper_kwargs['crawl_delay'] = processing_config['crawl_delay']
    if 'max_pages' in processing_config:
        scraper_kwargs['max_pages'] = processing_config['max_pages']
    
    scraper = WebScraper(**scraper_kwargs)
    scraper.scrape_all()
    logger.info("Web scraping completed")


def run_transformation_step(
    config: Dict[str, Any],
    input_dir: Path,
    output_dir: Path,
    batch_size: int,
    skip_transform: bool
) -> None:
    """
    Execute content transformation step.
    
    Args:
        config: Configuration dictionary
        input_dir: Directory containing raw content
        output_dir: Output directory for transformed content
        batch_size: Batch size for LLM processing
        skip_transform: If True, skip this step
    """
    logger = logging.getLogger(__name__)
    
    if skip_transform:
        logger.info("Step 2: Skipping content transformation")
        return
    
    logger.info("Step 2: Starting content transformation with LLM...")
    llm_config = config.get('llm', {})
    
    transformer = ContentTransformer(
        llm_config=llm_config,
        input_dir=input_dir,
        output_dir=output_dir,
        batch_size=batch_size
    )
    transformer.transform_all()
    logger.info("Content transformation completed")


def run_dataset_generation_step(
    config: Dict[str, Any],
    transformed_dir: Path,
    dataset_type: str
) -> None:
    """
    Execute dataset generation step.
    
    Args:
        config: Configuration dictionary
        transformed_dir: Directory containing transformed content
        dataset_type: Type of dataset to generate ('all' or specific type)
    """
    logger = logging.getLogger(__name__)
    
    logger.info("Step 3: Generating datasets...")
    dataset_generator = DatasetGenerator(
        transformed_dir=transformed_dir,
        config=config
    )
    
    # Determine which datasets to generate
    dataset_types = (
        ['instruction-response', 'summary', 'faq', 'guide', 'explanation', 'multi-turn']
        if dataset_type == 'all'
        else [dataset_type]
    )
    
    # Generate each dataset type
    for ds_type in dataset_types:
        logger.info(f"  Generating {ds_type} dataset...")
        method_name = f'generate_{ds_type.replace("-", "_")}'
        getattr(dataset_generator, method_name)()
    
    logger.info(f"Dataset generation completed ({len(dataset_types)} type(s))")


def run_export_step(
    dataset_dir: Path,
    output_dir: Path
) -> None:
    """
    Execute JSONL export step.
    
    Args:
        dataset_dir: Directory containing generated datasets
        output_dir: Directory for final JSONL export
    """
    logger = logging.getLogger(__name__)
    
    logger.info("Step 4: Exporting datasets to JSONL...")
    exporter = JSONLExporter(
        dataset_dir=dataset_dir,
        output_dir=output_dir
    )
    exporter.export_all()
    logger.info("JSONL export completed")


def main():
    """
    Main orchestrator for the LLM training data generation pipeline.
    
    Orchestrates the following steps:
    1. Parse and validate command-line arguments
    2. Setup logging and validate environment
    3. Load configuration from file
    4. Create output directories
    5. Scrape websites
    6. Transform content using LLM
    7. Generate datasets
    8. Export to JSONL format
    """
    try:
        # Step 1: Parse arguments
        args = parse_arguments()
        
        # Step 2: Validate arguments
        if not validate_arguments(args):
            sys.exit(1)
        
        # Step 3: Setup pipeline (logging and environment validation)
        logger = setup_pipeline(args.log_level)
        
        # Step 4: Load configuration
        config = load_configuration(args.config)
        
        # Step 5: Create output directories
        output_dir, raw_content_dir, transformed_dir = create_directories(args.output)
        
        # Step 6: Run web scraping
        run_scraping_step(
            config=config,
            output_dir=raw_content_dir,
            workers=args.workers,
            skip_scrape=args.skip_scrape
        )
        
        # Step 7: Run content transformation
        run_transformation_step(
            config=config,
            input_dir=raw_content_dir,
            output_dir=transformed_dir,
            batch_size=args.batch_size,
            skip_transform=args.skip_transform
        )
        
        # Step 8: Run dataset generation
        run_dataset_generation_step(
            config=config,
            transformed_dir=transformed_dir,
            dataset_type=args.dataset_type
        )
        
        # Step 9: Run export
        run_export_step(
            dataset_dir=output_dir / 'datasets',
            output_dir=output_dir
        )
        
        # Final summary
        logger.info("=" * 70)
        logger.info("Pipeline completed successfully!")
        logger.info(f"Datasets exported to: {output_dir}")
        logger.info("=" * 70)
    
    except ValidationError as e:
        logging.error(f"Configuration validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

"""
JSONL Export Module

Handles exporting datasets to JSONL format compatible with UnSloth
and Hugging Face. Includes validation and format conversion utilities.

UnSloth expects JSONL format:
    - One JSON object per line
    - Each line is a complete, valid JSON object
    - Standard fields: instruction, input, output (or similar variants)
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib

logger = logging.getLogger(__name__)


class JSONLExporter:
    """
    Exports datasets to JSONL format for UnSloth/Hugging Face compatibility.
    
    Handles format conversion, validation, and metadata generation.
    Supports multiple schema formats for different use cases.
    """
    
    def __init__(self, dataset_dir: Path, output_dir: Path):
        """
        Initialize JSONL exporter.
        
        Args:
            dataset_dir: Directory containing JSON dataset files
            output_dir: Directory to save JSONL files
        """
        self.dataset_dir = Path(dataset_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"JSONLExporter initialized, output: {self.output_dir}")
    
    def export_all(self) -> None:
        """
        Export all datasets to JSONL format.
        
        Scans dataset directory and exports all JSONL files,
        also generating combined dataset and metadata.
        """
        jsonl_files = list(self.dataset_dir.glob('*.jsonl'))
        
        if not jsonl_files:
            logger.warning(f"No JSONL files found in {self.dataset_dir}")
            return
        
        logger.info(f"Exporting {len(jsonl_files)} JSONL files")
        
        # Export individual datasets
        for jsonl_file in jsonl_files:
            self._export_single(jsonl_file)
        
        # Create combined dataset
        self._combine_datasets(jsonl_files)
        
        # Generate dataset summary and statistics
        self._generate_summary(jsonl_files)
        
        logger.info("Export completed")
    
    def _export_single(self, jsonl_file: Path) -> None:
        """
        Export a single JSONL file with validation and formatting.
        
        Args:
            jsonl_file: Path to source JSONL file
        """
        output_file = self.output_dir / f"final_{jsonl_file.name}"
        
        valid_count = 0
        invalid_count = 0
        
        with open(jsonl_file, 'r', encoding='utf-8') as infile:
            with open(output_file, 'w', encoding='utf-8') as outfile:
                for line_num, line in enumerate(infile, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        # Validate and normalize
                        validated_data = self._validate_and_normalize(data)
                        outfile.write(json.dumps(validated_data, ensure_ascii=False) + '\n')
                        valid_count += 1
                    except json.JSONDecodeError as e:
                        logger.warning(f"Invalid JSON in {jsonl_file} line {line_num}: {e}")
                        invalid_count += 1
                    except Exception as e:
                        logger.warning(f"Error processing {jsonl_file} line {line_num}: {e}")
                        invalid_count += 1
        
        logger.info(
            f"Exported {jsonl_file.name}: {valid_count} valid, {invalid_count} invalid items"
        )
    
    def _validate_and_normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize data to UnSloth format.
        
        Ensures data has required fields:
        - instruction: The task or query
        - input: Optional input data
        - output: The expected response
        
        Supports multiple data structures:
        - Standard: instruction/question/topic/title + output/response/answer
        - Multi-turn: turns (list of {"role": "user/assistant", "content": "..."})
        
        Args:
            data: Raw data dictionary
            
        Returns:
            Normalized dictionary
            
        Raises:
            ValueError: If required fields are missing
        """
        normalized = {}
        
        # Handle multi-turn dialogues
        if 'turns' in data and isinstance(data['turns'], list) and len(data['turns']) > 0:
            turns = data['turns']
            
            # Extract first user message as instruction
            user_messages = [t.get('content', '') for t in turns if t.get('role') == 'user']
            assistant_messages = [t.get('content', '') for t in turns if t.get('role') == 'assistant']
            
            if user_messages:
                normalized['instruction'] = str(user_messages[0]).strip()
            
            if assistant_messages:
                # Combine all assistant responses
                normalized['output'] = '\n\n'.join(str(msg).strip() for msg in assistant_messages if msg)
            
            # If we successfully parsed a multi-turn dialogue, continue with output validation
            if 'instruction' in normalized and 'output' in normalized:
                normalized['input'] = ""
                if 'category' in data:
                    normalized['category'] = str(data['category']).lower()
                
                # Validate minimum lengths
                if len(normalized['instruction']) < 5:
                    raise ValueError("Instruction too short")
                if len(normalized['output']) < 10:
                    raise ValueError("Output too short")
                
                return normalized
            else:
                raise ValueError("Multi-turn dialogue missing user or assistant messages")
        
        # Handle different field name variations for instruction
        if 'instruction' in data:
            normalized['instruction'] = str(data['instruction']).strip()
        elif 'question' in data:
            normalized['instruction'] = str(data['question']).strip()
        elif 'topic' in data:
            normalized['instruction'] = f"Explain: {data['topic']}"
        elif 'title' in data:
            normalized['instruction'] = str(data['title']).strip()
        else:
            raise ValueError("Missing instruction/question/topic/title field")
        
        # Handle output/response/answer
        if 'output' in data:
            normalized['output'] = str(data['output']).strip()
        elif 'response' in data:
            normalized['output'] = str(data['response']).strip()
        elif 'answer' in data:
            normalized['output'] = str(data['answer']).strip()
        elif 'explanation' in data:
            normalized['output'] = str(data['explanation']).strip()
        elif 'steps' in data and isinstance(data['steps'], list):
            # Handle steps from guides - convert dicts to strings if needed
            steps_text = []
            for step in data['steps']:
                if isinstance(step, dict):
                    # Extract step title and description
                    step_num = step.get('step_number', '')
                    step_title = step.get('title', '')
                    step_desc = step.get('description', '')
                    step_str = f"Step {step_num}: {step_title}\n{step_desc}"
                    steps_text.append(step_str.strip())
                else:
                    # It's already a string
                    steps_text.append(str(step).strip())
            normalized['output'] = '\n\n'.join(steps_text)
        else:
            raise ValueError("Missing output/response/answer field")
        
        # Optional input field
        if 'input' in data and data['input']:
            normalized['input'] = str(data['input']).strip()
        else:
            normalized['input'] = ""
        
        # Preserve category for filtering/organization
        if 'category' in data:
            normalized['category'] = str(data['category']).lower()
        
        # Preserve source_url for traceability
        if 'source_url' in data:
            normalized['source_url'] = str(data['source_url']).strip()
        
        # Validate minimum lengths
        if len(normalized['instruction']) < 5:
            raise ValueError("Instruction too short")
        if len(normalized['output']) < 10:
            raise ValueError("Output too short")
        
        return normalized
    
    def _combine_datasets(self, jsonl_files: List[Path]) -> None:
        """
        Combine all exported datasets into a single comprehensive file.
        
        Args:
            jsonl_files: List of JSONL file paths
        """
        combined_file = self.output_dir / 'combined_training_data.jsonl'
        
        total_items = 0
        
        with open(combined_file, 'w', encoding='utf-8') as outfile:
            for jsonl_file in jsonl_files:
                export_file = self.output_dir / f"final_{jsonl_file.name}"
                
                if not export_file.exists():
                    continue
                
                with open(export_file, 'r', encoding='utf-8') as infile:
                    for line in infile:
                        outfile.write(line)
                        total_items += 1
        
        logger.info(f"Created combined dataset: {combined_file} ({total_items} items)")
    
    def _generate_summary(self, jsonl_files: List[Path]) -> None:
        """
        Generate dataset summary and statistics.
        
        Creates a comprehensive summary file with statistics and metadata.
        
        Args:
            jsonl_files: List of exported JSONL files
        """
        summary_file = self.output_dir / 'DATASET_SUMMARY.md'
        
        stats = {
            'datasets': {},
            'total_items': 0,
            'categories': {}
        }
        
        # Collect statistics
        for jsonl_file in jsonl_files:
            export_file = self.output_dir / f"final_{jsonl_file.name}"
            
            if not export_file.exists():
                continue
            
            dataset_stats = {
                'filename': export_file.name,
                'items': 0,
                'categories': {}
            }
            
            with open(export_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        dataset_stats['items'] += 1
                        stats['total_items'] += 1
                        
                        category = data.get('category', 'unknown')
                        dataset_stats['categories'][category] = dataset_stats['categories'].get(category, 0) + 1
                        stats['categories'][category] = stats['categories'].get(category, 0) + 1
                    except:
                        pass
            
            stats['datasets'][jsonl_file.stem] = dataset_stats
        
        # Write summary
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("# Training Dataset Summary\n\n")
            f.write("## Overview\n\n")
            f.write(f"- **Total Items**: {stats['total_items']}\n")
            f.write(f"- **Datasets**: {len(stats['datasets'])}\n")
            f.write(f"- **Categories**: {', '.join(stats['categories'].keys())}\n\n")
            
            f.write("## Dataset Breakdown\n\n")
            for dataset_name, dataset_stats in stats['datasets'].items():
                f.write(f"### {dataset_name}\n\n")
                f.write(f"- Items: {dataset_stats['items']}\n")
                if dataset_stats['categories']:
                    f.write("- Categories:\n")
                    for cat, count in dataset_stats['categories'].items():
                        f.write(f"  - {cat}: {count}\n")
                f.write("\n")
            
            f.write("## Category Distribution\n\n")
            for category, count in stats['categories'].items():
                percentage = (count / stats['total_items'] * 100) if stats['total_items'] > 0 else 0
                f.write(f"- {category}: {count} ({percentage:.1f}%)\n")
            
            f.write("\n## Format\n\n")
            f.write("All datasets are in JSONL format, compatible with:\n")
            f.write("- UnSloth\n")
            f.write("- Hugging Face Datasets\n")
            f.write("- LLaMA Training Scripts\n\n")
            
            f.write("## JSONL Schema\n\n")
            f.write("```json\n")
            f.write('{\n')
            f.write('  "instruction": "The task or query",\n')
            f.write('  "input": "Optional input data",\n')
            f.write('  "output": "The expected response",\n')
            f.write('  "category": "Dataset category"\n')
            f.write('}\n')
            f.write("```\n\n")
            
            f.write("## Usage with UnSloth\n\n")
            f.write("```python\n")
            f.write("from unsloth import FastLanguageModel\n")
            f.write("from datasets import load_dataset\n\n")
            f.write("# Load dataset\n")
            f.write("dataset = load_dataset('json', data_files='combined_training_data.jsonl')\n\n")
            f.write("# Fine-tune with UnSloth\n")
            f.write("# ... training code ...\n")
            f.write("```\n")
        
        logger.info(f"Generated summary: {summary_file}")

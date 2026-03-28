"""
Dataset Generation Module

Generates various types of training datasets from transformed content:
    - Instruction-Response pairs
    - Summaries
    - FAQs
    - Step-by-step guides
    - Explanations
    - Multi-turn dialogues

All datasets are generated in formats compatible with UnSloth and Hugging Face.
"""

import logging
import json
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class InstructionResponsePair:
    """Instruction-Response pair for training."""
    instruction: str
    response: str
    category: str = "general"


@dataclass
class FAQItem:
    """FAQ pair for training."""
    question: str
    answer: str
    category: str = "faq"


@dataclass
class GuideItem:
    """Step-by-step guide for training."""
    title: str
    steps: List[str]
    category: str = "guide"


@dataclass
class ExplanationItem:
    """Explanation for training."""
    topic: str
    explanation: str
    category: str = "explanation"


@dataclass
class MultiTurnDialogue:
    """Multi-turn dialogue for training."""
    turns: List[Dict[str, str]]  # List of {"role": "user"/"assistant", "content": "..."}
    category: str = "multi-turn"


class DatasetGenerator:
    """
    Generates multiple types of training datasets from transformed content.
    
    Creates instruction-response data compatible with UnSloth and Hugging Face
    formats for efficient model fine-tuning.
    """
    
    def __init__(self, transformed_dir: Path, config: Dict[str, Any]):
        """
        Initialize dataset generator.
        
        Args:
            transformed_dir: Directory containing transformed content
            config: Configuration dictionary
        """
        self.transformed_dir = Path(transformed_dir)
        self.config = config
        self.datasets_dir = self.transformed_dir.parent / 'datasets'
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"DatasetGenerator initialized")
    
    def generate_instruction_response(self) -> None:
        """
        Generate instruction-response pairs from content.
        
        Creates pairs suitable for instruction-following model training.
        """
        logger.info("Generating instruction-response dataset...")
        
        pairs = []
        
        for content_file in self.transformed_dir.glob('transformed_*.json'):
            with open(content_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            meta = data['metadata']
            transformations = data.get('transformations', {})
            
            # From summaries
            for summary in transformations.get('summaries', []):
                pairs.append(InstructionResponsePair(
                    instruction=f"Summarize the following topic: {meta['name']}",
                    response=summary,
                    category="summary"
                ))
            
            # From explanations
            for explanation in transformations.get('explanations', []):
                pairs.append(InstructionResponsePair(
                    instruction=f"Explain the following concept from {meta['name']}",
                    response=explanation,
                    category="explanation"
                ))
            
            # From guides
            for guide in transformations.get('guides', []):
                if isinstance(guide, dict) and 'steps' in guide:
                    # Convert step dictionaries to readable text
                    steps_text_parts = []
                    for step in guide['steps']:
                        if isinstance(step, dict):
                            step_num = step.get('step_number', '')
                            step_title = step.get('title', '')
                            step_desc = step.get('description', '')
                            if step_num:
                                step_text = f"Step {step_num}: {step_title}. {step_desc}"
                            else:
                                step_text = f"{step_title}. {step_desc}" if step_title else step_desc
                            steps_text_parts.append(step_text)
                        else:
                            steps_text_parts.append(str(step))
                    
                    steps_text = '\n'.join(steps_text_parts)
                    pairs.append(InstructionResponsePair(
                        instruction=f"Provide a step-by-step guide for: {guide.get('title', meta['name'])}",
                        response=steps_text,
                        category="guide"
                    ))
        
        self._save_dataset('instruction_response', pairs)
        logger.info(f"Generated {len(pairs)} instruction-response pairs")
    
    def generate_summary(self) -> None:
        """Generate summary-focused dataset."""
        logger.info("Generating summary dataset...")
        
        items = []
        
        for content_file in self.transformed_dir.glob('transformed_*.json'):
            with open(content_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            transformations = data.get('transformations', {})
            
            for i, summary in enumerate(transformations.get('summaries', []), 1):
                items.append(InstructionResponsePair(
                    instruction=f"Summarize: Topic {i}",
                    response=summary,
                    category="summary"
                ))
        
        self._save_dataset('summary', items)
        logger.info(f"Generated {len(items)} summary items")
    
    def generate_faq(self) -> None:
        """Generate FAQ-focused dataset from extracted Q&A pairs."""
        logger.info("Generating FAQ dataset...")
        
        items = []
        
        for content_file in self.transformed_dir.glob('transformed_*.json'):
            with open(content_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            transformations = data.get('transformations', {})
            
            for faq_item in transformations.get('faqs', []):
                if isinstance(faq_item, dict):
                    items.append(FAQItem(
                        question=faq_item.get('question', ''),
                        answer=faq_item.get('answer', ''),
                        category="faq"
                    ))
        
        self._save_dataset('faq', items)
        logger.info(f"Generated {len(items)} FAQ items")
    
    def generate_guide(self) -> None:
        """Generate step-by-step guide dataset."""
        logger.info("Generating guide dataset...")
        
        items = []
        
        for content_file in self.transformed_dir.glob('transformed_*.json'):
            with open(content_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            transformations = data.get('transformations', {})
            
            for guide in transformations.get('guides', []):
                if isinstance(guide, dict):
                    items.append(GuideItem(
                        title=guide.get('title', 'Untitled'),
                        steps=guide.get('steps', []),
                        category="guide"
                    ))
        
        self._save_dataset('guide', items)
        logger.info(f"Generated {len(items)} guide items")
    
    def generate_explanation(self) -> None:
        """Generate explanation-focused dataset."""
        logger.info("Generating explanation dataset...")
        
        items = []
        
        for content_file in self.transformed_dir.glob('transformed_*.json'):
            with open(content_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            transformations = data.get('transformations', {})
            meta = data['metadata']
            
            for i, explanation in enumerate(transformations.get('explanations', []), 1):
                items.append(ExplanationItem(
                    topic=f"{meta['name']} - Concept {i}",
                    explanation=explanation,
                    category="explanation"
                ))
        
        self._save_dataset('explanation', items)
        logger.info(f"Generated {len(items)} explanation items")
    
    def generate_multi_turn(self) -> None:
        """
        Generate multi-turn dialogue dataset.
        
        Creates realistic conversation flows by combining content
        into interactive dialogue formats.
        """
        logger.info("Generating multi-turn dialogue dataset...")
        
        items = []
        
        for content_file in self.transformed_dir.glob('transformed_*.json'):
            with open(content_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            meta = data['metadata']
            transformations = data.get('transformations', {})
            
            # Create dialogue from FAQ
            for faq_item in transformations.get('faqs', []):
                if isinstance(faq_item, dict):
                    dialogue = MultiTurnDialogue(
                        turns=[
                            {"role": "user", "content": faq_item.get('question', '')},
                            {"role": "assistant", "content": faq_item.get('answer', '')}
                        ],
                        category="multi-turn"
                    )
                    items.append(dialogue)
            
            # Create dialogue from summaries and explanations
            summaries = transformations.get('summaries', [])
            explanations = transformations.get('explanations', [])
            
            if summaries and explanations:
                for summary in summaries[:1]:  # Use first summary
                    for explanation in explanations[:1]:  # Use first explanation
                        dialogue = MultiTurnDialogue(
                            turns=[
                                {"role": "user", "content": f"Can you summarize {meta['name']}?"},
                                {"role": "assistant", "content": summary},
                                {"role": "user", "content": "Can you explain that in more detail?"},
                                {"role": "assistant", "content": explanation}
                            ],
                            category="multi-turn"
                        )
                        items.append(dialogue)
        
        self._save_dataset('multi_turn', items)
        logger.info(f"Generated {len(items)} multi-turn dialogues")
    
    def _save_dataset(self, dataset_type: str, items: List[Any]) -> None:
        """
        Save dataset items in both raw and JSONL formats.
        
        Args:
            dataset_type: Type of dataset (instruction_response, faq, etc)
            items: List of dataset items
        """
        if not items:
            logger.warning(f"No items to save for {dataset_type}")
            return
        
        # Determine output format
        output_file = self.datasets_dir / f"{dataset_type}.jsonl"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in items:
                # Convert dataclass to dict
                if hasattr(item, '__dataclass_fields__'):
                    item_dict = asdict(item)
                else:
                    item_dict = item
                
                f.write(json.dumps(item_dict, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved {len(items)} items to {output_file}")
    
    def _create_multipart_dialogue(
        self,
        initial_query: str,
        response: str,
        followup_queries: List[str],
        followup_responses: List[str]
    ) -> MultiTurnDialogue:
        """
        Create a multi-turn dialogue from individual parts.
        
        Args:
            initial_query: First user query
            response: Initial response
            followup_queries: List of follow-up questions
            followup_responses: List of follow-up responses
            
        Returns:
            MultiTurnDialogue with complete conversation
        """
        turns = [
            {"role": "user", "content": initial_query},
            {"role": "assistant", "content": response}
        ]
        
        for query, resp in zip(followup_queries, followup_responses):
            turns.append({"role": "user", "content": query})
            turns.append({"role": "assistant", "content": resp})
        
        return MultiTurnDialogue(turns=turns, category="multi-turn")

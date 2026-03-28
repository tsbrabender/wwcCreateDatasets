"""
Content Transformation Module

Uses LLM to transform raw web content into structured training datasets.
Supports multiple LLM providers (OpenAI, Anthropic, Local/Ollama).

Transformations include:
    - Summarization
    - Explanation generation
    - FAQ extraction
    - Step-by-step guide creation
    - Multi-turn dialogue generation
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    LOCAL = "local"


class ContentTransformer:
    """
    Transforms raw content using LLM into structured datasets.
    
    Supports multiple LLM providers and can process content in batches
    for efficiency. Stores intermediate results for debugging and reuse.
    """
    
    def __init__(
        self,
        llm_config: Dict[str, Any],
        input_dir: Path,
        output_dir: Path,
        batch_size: int = 16
    ):
        """
        Initialize content transformer.
        
        Args:
            llm_config: LLM configuration dictionary
            input_dir: Directory containing raw content
            output_dir: Directory to save transformed content
            batch_size: Number of items to process in batch
        """
        self.llm_config = llm_config
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.batch_size = batch_size
        
        self._initialize_llm_client()
        
        logger.info(f"ContentTransformer initialized with {self.llm_config.get('provider', 'unknown')} provider")
    
    def _initialize_llm_client(self) -> None:
        """
        Initialize LLM client based on configuration.
        
        This method should be implemented to support different providers.
        For now, it provides a structure for imports.
        """
        provider = self.llm_config.get('provider', 'openai').lower()
        
        try:
            if provider == 'openai':
                from openai import OpenAI
                self.client = OpenAI(api_key=self.llm_config.get('api_key'))
            elif provider == 'anthropic':
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.llm_config.get('api_key'))
            elif provider in ['ollama', 'local']:
                import ollama
                self.client = ollama.Client(host=self.llm_config.get('host', 'http://localhost:11434'))
            else:
                logger.warning(f"Unknown LLM provider: {provider}")
                self.client = None
        
        except ImportError as e:
            logger.warning(f"Could not import LLM provider library: {e}")
            self.client = None
    
    def transform_all(self) -> None:
        """
        Transform all raw content files in input directory.
        
        Iterates through all JSON files in input directory and transforms them.
        """
        content_files = list(self.input_dir.glob('*.json'))
        
        if not content_files:
            logger.warning(f"No content files found in {self.input_dir}")
            return
        
        logger.info(f"Found {len(content_files)} content files to transform")
        
        for content_file in content_files:
            try:
                self._transform_file(content_file)
            except Exception as e:
                logger.error(f"Error transforming {content_file}: {e}")
    
    def _transform_file(self, filepath: Path) -> None:
        """
        Transform a single content file.
        
        Args:
            filepath: Path to content JSON file
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metadata = data['metadata']
        content = data['content']
        
        logger.info(f"Transforming: {metadata['name']}")
        
        # Split content into chunks if necessary
        chunks = self._chunk_content(content)
        
        transformed_data = {
            'metadata': metadata,
            'transformations': {}
        }
        
        # Get source URL from metadata
        source_url = metadata.get('url', 'unknown')
        
        # Generate different types of content
        for chunk in chunks:
            summary = self._generate_summary(chunk, source_url)
            explanation = self._generate_explanation(chunk, source_url)
            faqs = self._generate_faq(chunk, source_url)
            guide = self._generate_guide(chunk, source_url)
            
            if summary:
                transformed_data['transformations'].setdefault('summaries', []).append(summary)
            if explanation:
                transformed_data['transformations'].setdefault('explanations', []).append(explanation)
            if faqs:
                transformed_data['transformations'].setdefault('faqs', []).extend(faqs)
            if guide:
                transformed_data['transformations'].setdefault('guides', []).append(guide)
        
        # Save transformed content
        output_file = self.output_dir / f"transformed_{filepath.name}"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transformed_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved transformed content to: {output_file}")
    
    def _chunk_content(self, content: str, chunk_size: int = 2000) -> List[str]:
        """
        Split content into manageable chunks.
        
        Args:
            content: Full content text
            chunk_size: Maximum characters per chunk
            
        Returns:
            List of content chunks
        """
        chunks = []
        current_chunk = ""
        
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) < chunk_size:
                current_chunk += paragraph + '\n\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph + '\n\n'
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _generate_summary(self, content: str, source_url: str = 'unknown') -> Optional[Dict[str, Any]]:
        """
        Generate a summary of the content.
        
        Args:
            content: Content text to summarize
            source_url: URL of the source document
            
        Returns:
            Dictionary with summary and source_url or None if generation fails
        """
        if not self.client:
            logger.warning("LLM client not initialized, skipping summary generation")
            return None
        
        prompt = f"""Create a concise summary of the following content in 2-3 sentences:

{content[:1000]}

Summary:"""
        
        try:
            summary_text = self._call_llm(prompt)
            return {
                'text': summary_text,
                'source_url': source_url
            }
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return None
    
    def _generate_explanation(self, content: str, source_url: str = 'unknown') -> Optional[Dict[str, Any]]:
        """
        Generate a detailed explanation of the content.
        
        Args:
            content: Content text to explain
            source_url: URL of the source document
            
        Returns:
            Dictionary with explanation and source_url or None if generation fails
        """
        if not self.client:
            return None
        
        prompt = f"""Provide a detailed explanation of the following concept:

{content[:1000]}

Explanation:"""
        
        try:
            explanation_text = self._call_llm(prompt)
            return {
                'text': explanation_text,
                'source_url': source_url
            }
        except Exception as e:
            logger.error(f"Explanation generation failed: {e}")
            return None
    
    def _generate_faq(self, content: str, source_url: str = 'unknown') -> Optional[List[Dict[str, Any]]]:
        """
        Extract or generate FAQ pairs from content.
        
        Args:
            content: Content to generate FAQs from
            source_url: URL of the source document
            
        Returns:
            List of Q&A dictionaries with source_url or None if generation fails
        """
        if not self.client:
            return None
        
        prompt = f"""Generate 3-5 frequently asked questions and answers based on this content:

{content[:1000]}

Format as JSON:
[
  {{"question": "...", "answer": "..."}}
]

Response:"""
        
        try:
            response = self._call_llm(prompt)
            # Extract JSON from response
            import json as json_lib
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                faqs = json_lib.loads(response[json_start:json_end])
                # Sanitize FAQ text and add source_url to each FAQ
                for faq in faqs:
                    if 'question' in faq and isinstance(faq['question'], str):
                        faq['question'] = self._sanitize_text(faq['question'])
                    if 'answer' in faq and isinstance(faq['answer'], str):
                        faq['answer'] = self._sanitize_text(faq['answer'])
                    faq['source_url'] = source_url
                return faqs
            return None
        except Exception as e:
            logger.error(f"FAQ generation failed: {e}")
            return None
    
    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize text by escaping control characters for JSON serialization.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text safe for JSON serialization
        """
        if not text:
            return ""
        # Replace literal newlines with space, tabs with space
        text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        # Remove other control characters
        text = ''.join(char if ord(char) >= 32 or char in '\n\r\t' else '' for char in text)
        # Clean up multiple spaces
        text = ' '.join(text.split())
        return text.strip()
    
    def _generate_guide(self, content: str, source_url: str = 'unknown') -> Optional[Dict[str, Any]]:
        """
        Generate a step-by-step guide from content.
        
        Args:
            content: Content to convert to guide format
            source_url: URL of the source document
            
        Returns:
            Guide dictionary with steps and source_url or None if generation fails
        """
        if not self.client:
            return None
        
        prompt = f"""Convert the following content into a step-by-step guide:

{content[:1000]}

Format as JSON:
{{
  "title": "...",
  "steps": [
    {{"step_number": 1, "title": "...", "description": "..."}},
  ]
}}

Response:"""
        
        try:
            response = self._call_llm(prompt)
            import json as json_lib
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                guide = json_lib.loads(response[json_start:json_end])
                
                # Sanitize title and step contents
                if 'title' in guide and isinstance(guide['title'], str):
                    guide['title'] = self._sanitize_text(guide['title'])
                
                if 'steps' in guide and isinstance(guide['steps'], list):
                    for step in guide['steps']:
                        if isinstance(step, dict):
                            if 'title' in step and isinstance(step['title'], str):
                                step['title'] = self._sanitize_text(step['title'])
                            if 'description' in step and isinstance(step['description'], str):
                                step['description'] = self._sanitize_text(step['description'])
                
                guide['source_url'] = source_url
                return guide
            return None
        except Exception as e:
            logger.error(f"Guide generation failed: {e}")
            return None
    
    def _call_llm(self, prompt: str, max_tokens: int = 1024) -> Optional[str]:
        """
        Make a call to the configured LLM.
        
        Args:
            prompt: Prompt text
            max_tokens: Maximum tokens in response
            
        Returns:
            LLM response or None if call fails
        """
        if not self.client:
            return None
        
        try:
            provider = self.llm_config.get('provider', 'openai').lower()
            
            if provider == 'openai':
                response = self.client.chat.completions.create(
                    model=self.llm_config.get('model', 'gpt-3.5-turbo'),
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=self.llm_config.get('temperature', 0.7)
                )
                return response.choices[0].message.content
            
            elif provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.llm_config.get('model', 'claude-3-sonnet-20240229'),
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            elif provider in ['ollama', 'local']:
                response = self.client.generate(
                    model=self.llm_config.get('model', 'llama2'),
                    prompt=prompt,
                    stream=False
                )
                return response['response']
            
            else:
                logger.error(f"Unknown LLM provider: {provider}")
                return None
        
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            return None

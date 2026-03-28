"""
Configuration Management Module

Handles loading, parsing, and validating configuration files for the LLM
training data pipeline. Supports YAML format with comprehensive validation.

Configuration Structure:
    sources:
        - name: str
          url: str
          scrape_type: str (web, pdf, api)
          content_selector: str
          
    llm:
        provider: str (openai, anthropic, local)
        model: str
        api_key: str (optional, can use env vars)
        
    output:
        format: str (jsonl)
        include_metadata: bool
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml


class ValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


class ConfigLoader:
    """
    Loads and validates LLM training data pipeline configuration.
    
    Supports YAML configuration files with validation of all required fields.
    Environment variables can be used for sensitive data like API keys.
    """
    
    REQUIRED_SOURCE_FIELDS = ['name', 'url', 'scrape_type']
    SUPPORTED_SCRAPE_TYPES = ['web', 'pdf', 'api']
    SUPPORTED_LLM_PROVIDERS = ['openai', 'anthropic', 'local', 'ollama']
    
    def __init__(self, config_path: str):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to YAML configuration file
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    def load(self) -> Dict[str, Any]:
        """
        Load and validate configuration from YAML file.
        
        Returns:
            Dictionary containing validated configuration
            
        Raises:
            ValidationError: If configuration is invalid
            yaml.YAMLError: If YAML parsing fails
        """
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValidationError(f"Invalid YAML format: {e}")
        
        if config is None:
            raise ValidationError("Configuration file is empty")
        
        # Validate top-level structure
        self._validate_structure(config)
        
        # Validate sources
        if 'sources' in config:
            self._validate_sources(config['sources'])
        
        # Validate LLM configuration
        if 'llm' in config:
            self._validate_llm_config(config['llm'])
        
        # Apply environment variable substitution
        self._substitute_env_vars(config)
        
        return config
    
    def _validate_structure(self, config: Dict[str, Any]) -> None:
        """
        Validate top-level configuration structure.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ValidationError: If structure is invalid
        """
        if not isinstance(config, dict):
            raise ValidationError("Configuration root must be a dictionary")
        
        # At least one of sources or llm must be present
        if not any(key in config for key in ['sources', 'llm']):
            raise ValidationError("Configuration must include 'sources' or 'llm'")
    
    def _validate_sources(self, sources: List[Dict[str, Any]]) -> None:
        """
        Validate sources configuration.
        
        Args:
            sources: List of source configurations
            
        Raises:
            ValidationError: If any source is invalid
        """
        if not isinstance(sources, list):
            raise ValidationError("'sources' must be a list")
        
        if len(sources) == 0:
            raise ValidationError("'sources' list must not be empty")
        
        for idx, source in enumerate(sources):
            if not isinstance(source, dict):
                raise ValidationError(f"Source {idx} must be a dictionary")
            
            # Check required fields
            for field in self.REQUIRED_SOURCE_FIELDS:
                if field not in source:
                    raise ValidationError(f"Source {idx} missing required field: {field}")
            
            # Validate URL format
            if not self._is_valid_url(source['url']):
                raise ValidationError(f"Source {idx} has invalid URL: {source['url']}")
            
            # Validate scrape type
            if source['scrape_type'] not in self.SUPPORTED_SCRAPE_TYPES:
                raise ValidationError(
                    f"Source {idx} has invalid scrape_type: {source['scrape_type']}. "
                    f"Must be one of {self.SUPPORTED_SCRAPE_TYPES}"
                )
    
    def _validate_llm_config(self, llm_config: Dict[str, Any]) -> None:
        """
        Validate LLM configuration.
        
        Args:
            llm_config: LLM configuration dictionary
            
        Raises:
            ValidationError: If LLM config is invalid
        """
        if not isinstance(llm_config, dict):
            raise ValidationError("'llm' must be a dictionary")
        
        # Provider is recommended
        if 'provider' in llm_config:
            if llm_config['provider'] not in self.SUPPORTED_LLM_PROVIDERS:
                raise ValidationError(
                    f"LLM provider '{llm_config['provider']}' not supported. "
                    f"Must be one of {self.SUPPORTED_LLM_PROVIDERS}"
                )
        
        # Model is required if provider is specified
        if 'provider' in llm_config and 'model' not in llm_config:
            raise ValidationError("'llm.model' required when 'llm.provider' is specified")
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Validate URL format.
        
        Args:
            url: URL string to validate
            
        Returns:
            bool: True if URL format is valid
        """
        url_pattern = re.compile(
            r'^https?://'  # HTTP or HTTPS
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # Domain
            r'localhost|'  # Localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # Optional port
            r'(?:/?|[/?]\S+)$',
            re.IGNORECASE
        )
        return url_pattern.match(url) is not None
    
    def _substitute_env_vars(self, config: Dict[str, Any]) -> None:
        """
        Substitute environment variables in configuration.
        
        Environment variables should be referenced as ${VAR_NAME} in config.
        
        Args:
            config: Configuration dictionary (modified in place)
        """
        def substitute_value(value: Any) -> Any:
            """Recursively substitute environment variables in values."""
            if isinstance(value, str):
                # Replace ${VAR} with environment variable value
                def replace_env(match):
                    var_name = match.group(1)
                    return os.getenv(var_name, match.group(0))
                
                return re.sub(r'\$\{([^}]+)\}', replace_env, value)
            
            elif isinstance(value, dict):
                return {k: substitute_value(v) for k, v in value.items()}
            
            elif isinstance(value, list):
                return [substitute_value(v) for v in value]
            
            return value
        
        # Apply substitution to all config values
        for key, value in list(config.items()):
            config[key] = substitute_value(value)

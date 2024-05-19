# config/config_loader.py
# This module provides a function to load configurations from config.yaml and .env files.
# It ensures that sensitive data is loaded from .env while other configurations are loaded from config.yaml.

import yaml
import os
from dotenv import load_dotenv

def load_config():
    """
    Load configurations from config.yaml and .env files.
    
    Returns:
        dict: A dictionary containing all configurations.
    """
    # Load environment variables from .env file
    load_dotenv()

    # Load configurations from config.yaml
    with open('config/config.yaml', 'r') as file:
        config = yaml.safe_load(file)

    # Replace placeholders with actual values from environment variables
    config['supabase']['url'] = os.getenv('SUPABASE_URL')
    config['supabase']['key'] = os.getenv('SUPABASE_KEY')
    config['api_keys']['anthropic'] = os.getenv('ANTHROPIC_API_KEY')
    config['api_keys']['groq'] = os.getenv('GROQ_API_KEY')

    return config

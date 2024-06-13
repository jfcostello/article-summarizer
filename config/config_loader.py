# config/config_loader.py
# This file loads configuration settings for the article summarizer application from both a YAML file and environment variables. It retrieves necessary configuration details for external services such as Supabase, API keys for Anthropic and Groq, and ensures Celery configuration defaults if not explicitly set in the configuration file.

import yaml
import os
from dotenv import load_dotenv


# Load environment variables and configuration settings from YAML file, 
# then merge and return them as a dictionary
def load_config():
    # Load environment variables from .env file
    load_dotenv()

    # Load configurations from config.yaml
    with open('config/config.yaml', 'r', encoding='utf-8') as file:
        config = yaml.safe_load(file) 

    # Replace placeholders with actual values from environment variables
    config['supabase']['url'] = os.getenv('SUPABASE_URL')
    config['supabase']['key'] = os.getenv('SUPABASE_KEY')
    config['api_keys']['anthropic'] = os.getenv('ANTHROPIC_API_KEY')
    config['api_keys']['groq'] = os.getenv('GROQ_API_KEY')
    config['api_keys']['gemini'] = os.getenv('GEMINI_API_KEY')

    # Ensure Celery configuration is loaded
    if 'celery' in config:
        config['celery']['broker_url'] = config['celery'].get('broker_url', 'pyamqp://guest@localhost//')
        config['celery']['result_backend'] = config['celery'].get('result_backend', 'rpc://')

    # Return the complete configuration dictionary
    return config

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

    # Ensure Celery configuration is loaded
    if 'celery' in config:
        config['celery']['broker_url'] = config['celery'].get('broker_url', 'pyamqp://guest@localhost//')
        config['celery']['result_backend'] = config['celery'].get('result_backend', 'rpc://')

    return config

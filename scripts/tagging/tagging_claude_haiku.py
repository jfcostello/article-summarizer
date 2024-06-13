# scripts/tagging/tagging_claude_haiku.py
import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.tagging_utils import process_articles
from utils.llm_utils import call_llm_api

if __name__ == "__main__":
    success = process_articles(
        script_name=os.path.basename(__file__),
        api_call_func=lambda content, systemPrompt: call_llm_api("claude-3-haiku-20240307", content, systemPrompt, client_type="anthropic")
    )
    sys.exit(0 if success else 1)

# scripts/tagging/tagging_gemini_flash.py
# This script tags summarized articles using Gemini's API and calling the Flash model. It stores the results in a Supabase database.
# It fetches articles needing tags, generates tags using a system prompt from a YAML configuration file,
# and logs the process and duration in Supabase.
import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from utils.tagging_utils import process_articles
from utils.llm_utils import call_llm_api

if __name__ == "__main__":
    success = process_articles(
        script_name=os.path.basename(__file__),
        api_call_func=lambda content, systemPrompt: call_llm_api(
            "gemini-1.5-flash",
            content,  
            systemPrompt,  
            client_type="gemini",
            max_tokens=8192  
        )
    )
    sys.exit(0 if success else 1)

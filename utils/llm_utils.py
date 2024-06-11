# utils/llm_utils.py
# This module provides utility functions to interact with various LLM APIs. Instead of calling your llm in your script, just define it, and send the variables over as needed
# Add new LLMs here as you use them, don't out them in other scripts

import os

def call_llm_api(model, content, systemPrompt, max_tokens=4000, temperature=0, client_type="default"):
    """
    Call a specified LLM API to summarize the content.

    Args:
        client (object): The LLM client.
        model (str): The model to use for the LLM.
        content (str): The content to summarize.
        systemPrompt (str): The system prompt for the LLM.
        max_tokens (int, optional): The maximum number of tokens. Defaults to 4000.
        temperature (int, optional): The temperature setting for the model. Defaults to 0.
        client_type (str, optional): The type of client (e.g., 'groq', 'anthropic', 'default'). Defaults to 'default'.

    Returns:
        object: The raw response content from the LLM API.
    """
    if client_type == "groq":
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        chat_completion = client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": content},
                {"role": "system", "content": systemPrompt}
            ]
        )
        return chat_completion
    elif client_type == "anthropic":
        from anthropic import Anthropic
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        chat_completion = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=systemPrompt,
            messages=[{"role": "user", "content": content}]
        )
        return chat_completion
    elif client_type == "gemini": 
        from google.generativeai import GenerativeModel  # Import GenerativeModel directly
        from google.generativeai import configure
        from google.generativeai.types import HarmCategory, HarmBlockThreshold

        configure(api_key=os.environ["GEMINI_API_KEY"])

        generation_config = {
            "temperature": temperature, 
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": max_tokens, 
            "response_mime_type": "text/plain",
        }

        gemini_model = GenerativeModel( 
            model_name=model,
            generation_config=generation_config,
            system_instruction=systemPrompt, 
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        )

        chat_session = gemini_model.start_chat() 

        chat_completion = chat_session.send_message(content)  


        return chat_completion 

    else:
        raise ValueError(f"Unsupported client type: {client_type}")

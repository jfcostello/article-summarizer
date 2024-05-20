# utils/llm_utils.py
# This module provides utility functions to interact with various LLM APIs.

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
    else:
        raise ValueError(f"Unsupported client type: {client_type}")

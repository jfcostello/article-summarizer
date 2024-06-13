# utils/llm_utils.py
# This module provides utility functions to interact with various LLM APIs. Instead of calling your llm in your script, 
# just define it, and send the variables over as needed
# This script also strips the response down to just the content from the LLM
# Add new LLMs here as you use them, don't put them in other scripts

import os

def call_llm_api(model, content, systemPrompt, max_tokens=4000, temperature=0, client_type="default"):
    """
    Call a specified LLM API to process the content (summarization or oitagging).

    Args:
        model (str): The model to use for the LLM.
        content (str): The content to be processed.
        systemPrompt (str): The system prompt for the LLM.
        max_tokens (int, optional): The maximum number of tokens. Defaults to 4000.
        temperature (int, optional): The temperature setting for the model. Defaults to 0.
        client_type (str, optional): The type of client (e.g., 'groq', 'anthropic', 'gemini'). 
                                     Defaults to 'default'.

    Returns:
        str or dict: The parsed response content from the LLM API. 
                      The format depends on the LLM and the task.
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

        # Parse the response for Groq
        response_content = chat_completion.choices[0].message.content
        return response_content
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

        # Parse the response for Anthropic - extracting content from 'text' field
        try:
            response_content = chat_completion.content[0].text  # Corrected variable name 
            return response_content
        except (IndexError, AttributeError) as e: 
            raise ValueError(f"Error parsing Anthropic response: {e}")
    elif client_type == "gemini": 
        from google.generativeai import GenerativeModel
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

        # Parse the response for Gemini - extracting content from 'text' field , which is nested in other fields in JSON
        try:
            response_content = chat_completion.candidates[0].content.parts[0].text
            return response_content
        except (IndexError, AttributeError) as e: 
            raise ValueError(f"Error parsing Gemini response: {e}")
    elif client_type == "replicate":
        # Set up for replicate which can call a bunch of LLMs. Commented out some unncessary additional code it sent, but we may need it for other models
        import replicate
        client = replicate.Client(api_token=os.getenv("REPLICATE_API_KEY"))
        output = client.run(
            model,
            input={
                "top_k": 0,
                "top_p": 0.95,
                "prompt": content, 
                "max_tokens": 4000,  
                "temperature": temperature,
                "system_prompt": systemPrompt,  
                #"length_penalty": 1,
                #"max_new_tokens": 512,  
                #"stop_sequences": "<|end_of_text|>,<|eot_id|>",
                #"prompt_template": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n",
                "presence_penalty": 0,
                "log_performance_metrics": False
            }
        )

        response_content = "".join(output) # Join the streamed output into a single string
        return response_content
    else:
        raise ValueError(f"Unsupported client type: {client_type}")
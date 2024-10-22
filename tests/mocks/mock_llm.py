# tests/mocks/mock_llm.py

def mock_llm_api_success(content, systemPrompt, client_type="anthropic", max_tokens=4000):
    """
    Mocked successful response from the LLM API.
    """
    if client_type == "anthropic":
        return {
            "IntroParagraph": "This is a mocked intro paragraph from Anthropic.",
            "BulletPointSummary": {
                "bulletPoints": [
                    {"point": "Mocked bullet point 1 from Anthropic."},
                    {"point": "Mocked bullet point 2 from Anthropic."}
                ]
            },
            "ConcludingParagraph": "This is a mocked concluding paragraph from Anthropic."
        }
    elif client_type == "gemini":
        return {
            "IntroParagraph": "This is a mocked intro paragraph from Gemini.",
            "BulletPointSummary": {
                "bulletPoints": [
                    {"point": "Mocked bullet point 1 from Gemini."},
                    {"point": "Mocked bullet point 2 from Gemini."}
                ]
            },
            "ConcludingParagraph": "This is a mocked concluding paragraph from Gemini."
        }
    elif client_type == "groq":
        return {
            "IntroParagraph": "This is a mocked intro paragraph from Groq.",
            "BulletPointSummary": {
                "bulletPoints": [
                    {"point": "Mocked bullet point 1 from Groq."},
                    {"point": "Mocked bullet point 2 from Groq."}
                ]
            },
            "ConcludingParagraph": "This is a mocked concluding paragraph from Groq."
        }
    elif client_type == "replicate":
        return {
            "IntroParagraph": "This is a mocked intro paragraph from Replicate.",
            "BulletPointSummary": {
                "bulletPoints": [
                    {"point": "Mocked bullet point 1 from Replicate."},
                    {"point": "Mocked bullet point 2 from Replicate."}
                ]
            },
            "ConcludingParagraph": "This is a mocked concluding paragraph from Replicate."
        }
    elif client_type == "openai":
        return {
            "IntroParagraph": "This is a mocked intro paragraph from AIML.",
            "BulletPointSummary": {
                "bulletPoints": [
                    {"point": "Mocked bullet point 1 from AIML."},
                    {"point": "Mocked bullet point 2 from AIML."}
                ]
            },
            "ConcludingParagraph": "This is a mocked concluding paragraph from AIML."
        }
    elif client_type == "togetherai":
        return {
            "IntroParagraph": "This is a mocked intro paragraph from TogetherAI.",
            "BulletPointSummary": {
                "bulletPoints": [
                    {"point": "Mocked bullet point 1 from TogetherAI."},
                    {"point": "Mocked bullet point 2 from TogetherAI."}
                ]
            },
            "ConcludingParagraph": "This is a mocked concluding paragraph from TogetherAI."
        }
    else:
        raise ValueError(f"Unsupported client type: {client_type}")

def mock_llm_api_error(content, systemPrompt, client_type="anthropic", max_tokens=4000):
    """
    Mocked error response from the LLM API.
    """
    raise Exception(f"Mocked LLM API error for client type: {client_type}")

def mock_llm_api_empty(content, systemPrompt, client_type="anthropic", max_tokens=4000):
    """
    Mocked empty response from the LLM API.
    """
    return {
        "IntroParagraph": "",
        "BulletPointSummary": {
            "bulletPoints": []
        },
        "ConcludingParagraph": ""
    }

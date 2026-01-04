import os
from typing import Any

# Example: Groq LLM and OpenAI LLM
try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None
    
    
def get_llm_instance(provider: str, model: str) -> Any:
    """
    Factory to return a ready-to-use LLM instance based on provider name.

    :param provider: 'groq' or 'openai'
    :param model: LLM model name
    :return: LLM instance ready to pass to MovieAgentService
    """

    provider = provider.lower()
    
    if provider == "groq":
        if ChatGroq is None:
            raise ImportError("langchain_groq not installed")
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set in environment")
        
        # Validate Groq model name format
        valid_groq_models = [
            "llama-3.1-8b-instant",
            "llama-3.1-70b-versatile", 
            "llama-3.2-3b",
            "mixtral-8x7b-32768"
        ]
        
        if model not in valid_groq_models:
            # Warn but don't fail - Groq might add new models
            print(f"Warning: Model '{model}' not in known Groq models. "
                  f"Known models: {valid_groq_models}")
        
        return ChatGroq(
            model=model,
            api_key=api_key,
            streaming=False,  # disable streaming to reduce function-call issues
        )
    
    elif provider == "openai":
        if ChatOpenAI is None:
            raise ImportError("langchain_openai not installed")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set in environment")
        return ChatOpenAI(
            model_name=model,
            openai_api_key=api_key,
            streaming=False,
        )

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
import os

def call_llm_api(prompt, model_provider, model_name, **kwargs):
    """
    Calls an LLM API (OpenAI or Anthropic) with the given prompt and model.

    Args:
        prompt (str): The prompt to send to the LLM.
        model_provider (str): The provider name, e.g., "openai" or "anthropic".
        model_name (str): The model name to use.
        **kwargs: Additional keyword arguments for the API call.

    Returns:
        str: The generated response from the LLM.

    Raises:
        ValueError: If the provider is not supported or required API key is missing.
    """
    if model_provider.lower() == "openai":
        try:
            import openai
        except ImportError:
            raise ImportError("Please install the openai package: pip install openai")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        return response.choices[0].message['content'].strip()
    elif model_provider.lower() == "anthropic":
        try:
            import anthropic
        except ImportError:
            raise ImportError("Please install the anthropic package: pip install anthropic")
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set.")
        client = anthropic.Anthropic(api_key=api_key)
        # For Claude v2 and above, use the new API
        # anthropic.Message API (Claude 2+)
        if hasattr(client, "messages"):
            response = client.messages.create(
                model=model_name,
                max_tokens=kwargs.get("max_tokens", 1024),
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        else:
            # Fallback for older anthropic API
            response = client.completions.create(
                model=model_name,
                prompt=f"\n\nHuman: {prompt}\n\nAssistant:",
                max_tokens_to_sample=kwargs.get("max_tokens", 1024),
                stop_sequences=kwargs.get("stop_sequences", ["\n\nHuman:"])
            )
            return response.completion.strip()
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")

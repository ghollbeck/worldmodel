import os
from datetime import datetime
from typing import Dict, Optional, Any
import json

# Cost tracking variables
cost_session = {
    "total_cost": 0.0,
    "api_calls": 0,
    "providers": {},
    "session_start": datetime.now(),
    "tokens_used": {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0
    }
}

# Provider pricing (per 1M tokens)
PROVIDER_PRICING = {
    "openai": {
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4o": {"input": 2.5, "output": 10.0},
        "gpt-4o-mini": {"input": 0.15, "output": 0.6},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-4-32k": {"input": 60.0, "output": 120.0},
        "gpt-3.5-turbo-16k": {"input": 3.0, "output": 4.0},
        "gpt-4-1106-preview": {"input": 10.0, "output": 30.0},
        "gpt-4-0125-preview": {"input": 10.0, "output": 30.0},
        "gpt-4-turbo-preview": {"input": 10.0, "output": 30.0},
        "default": {"input": 10.0, "output": 30.0}  # Fallback pricing
    },
    "anthropic": {
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
        "claude-3-5-sonnet-20240620": {"input": 3.0, "output": 15.0},
        "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
        "claude-3-5-haiku-20241022": {"input": 0.8, "output": 4.0},
        "claude-2.1": {"input": 8.0, "output": 24.0},
        "claude-2.0": {"input": 8.0, "output": 24.0},
        "claude-instant-1.2": {"input": 0.8, "output": 2.4},
        "default": {"input": 8.0, "output": 24.0}  # Fallback pricing
    }
}

def calculate_cost(provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate the cost for a specific API call"""
    provider_key = provider.lower()
    
    if provider_key not in PROVIDER_PRICING:
        return 0.0
    
    pricing = PROVIDER_PRICING[provider_key]
    
    # Find the right pricing for the model
    model_pricing = None
    for model_key in pricing:
        if model_key in model.lower():
            model_pricing = pricing[model_key]
            break
    
    if not model_pricing:
        model_pricing = pricing["default"]
    
    # Calculate cost (pricing is per 1M tokens)
    input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
    output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
    
    return input_cost + output_cost

def update_cost_session(provider: str, model: str, input_tokens: int, output_tokens: int, cost: float):
    """Update the global cost session tracking"""
    global cost_session
    
    cost_session["total_cost"] += cost
    cost_session["api_calls"] += 1
    cost_session["tokens_used"]["input_tokens"] += input_tokens
    cost_session["tokens_used"]["output_tokens"] += output_tokens
    cost_session["tokens_used"]["total_tokens"] += input_tokens + output_tokens
    
    # Track by provider
    if provider not in cost_session["providers"]:
        cost_session["providers"][provider] = {
            "cost": 0.0,
            "calls": 0,
            "models": {},
            "tokens": {"input": 0, "output": 0, "total": 0}
        }
    
    provider_data = cost_session["providers"][provider]
    provider_data["cost"] += cost
    provider_data["calls"] += 1
    provider_data["tokens"]["input"] += input_tokens
    provider_data["tokens"]["output"] += output_tokens
    provider_data["tokens"]["total"] += input_tokens + output_tokens
    
    # Track by model
    if model not in provider_data["models"]:
        provider_data["models"][model] = {
            "cost": 0.0,
            "calls": 0,
            "tokens": {"input": 0, "output": 0, "total": 0}
        }
    
    model_data = provider_data["models"][model]
    model_data["cost"] += cost
    model_data["calls"] += 1
    model_data["tokens"]["input"] += input_tokens
    model_data["tokens"]["output"] += output_tokens
    model_data["tokens"]["total"] += input_tokens + output_tokens

def log_cost_info(provider: str, model: str, input_tokens: int, output_tokens: int, cost: float):
    """Log cost information with emoji formatting"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"💰 [{timestamp}] API Cost - {provider}:{model}")
    print(f"   📊 Tokens: {input_tokens:,} in + {output_tokens:,} out = {input_tokens + output_tokens:,} total")
    print(f"   💵 Cost: ${cost:.6f}")
    print(f"   📈 Session Total: ${cost_session['total_cost']:.6f} ({cost_session['api_calls']} calls)")

def print_cost_summary():
    """Print a comprehensive cost summary"""
    global cost_session
    
    if cost_session["api_calls"] == 0:
        print("💰 No API calls made in this session")
        return
    
    session_duration = datetime.now() - cost_session["session_start"]
    
    print("\n" + "="*60)
    print("💰 INFERENCE COST SUMMARY")
    print("="*60)
    print(f"🕐 Session Duration: {session_duration}")
    print(f"📞 Total API Calls: {cost_session['api_calls']}")
    print(f"📊 Total Tokens: {cost_session['tokens_used']['total_tokens']:,}")
    print(f"   📥 Input Tokens: {cost_session['tokens_used']['input_tokens']:,}")
    print(f"   📤 Output Tokens: {cost_session['tokens_used']['output_tokens']:,}")
    print(f"💵 Total Cost: ${cost_session['total_cost']:.6f}")
    
    if cost_session['total_cost'] > 0:
        print(f"📈 Average Cost per Call: ${cost_session['total_cost'] / cost_session['api_calls']:.6f}")
        print(f"🎯 Cost per 1K Tokens: ${cost_session['total_cost'] / (cost_session['tokens_used']['total_tokens'] / 1000):.6f}")
    
    print("\n" + "="*40)
    print("📊 BREAKDOWN BY PROVIDER")
    print("="*40)
    
    for provider, data in cost_session["providers"].items():
        print(f"\n🔧 {provider.upper()}:")
        print(f"   💵 Cost: ${data['cost']:.6f}")
        print(f"   📞 Calls: {data['calls']}")
        print(f"   📊 Tokens: {data['tokens']['total']:,} ({data['tokens']['input']:,} in + {data['tokens']['output']:,} out)")
        
        if len(data["models"]) > 1:
            print(f"   🤖 Models:")
            for model, model_data in data["models"].items():
                print(f"      • {model}: ${model_data['cost']:.6f} ({model_data['calls']} calls, {model_data['tokens']['total']:,} tokens)")
        else:
            model_name = list(data["models"].keys())[0]
            print(f"   🤖 Model: {model_name}")
    
    print("\n" + "="*60)
    
    # Cost warnings
    if cost_session['total_cost'] > 1.0:
        print("⚠️  HIGH COST WARNING: Session cost exceeds $1.00")
    elif cost_session['total_cost'] > 0.1:
        print("⚡ MODERATE COST: Session cost exceeds $0.10")
    
    print("="*60)

def extract_usage_from_response(response: Any, provider: str) -> tuple[int, int]:
    """Extract token usage from API response"""
    input_tokens = 0
    output_tokens = 0
    
    try:
        if provider.lower() == "openai":
            if hasattr(response, 'usage'):
                usage = response.usage
                input_tokens = getattr(usage, 'prompt_tokens', 0)
                output_tokens = getattr(usage, 'completion_tokens', 0)
        elif provider.lower() == "anthropic":
            if hasattr(response, 'usage'):
                usage = response.usage
                input_tokens = getattr(usage, 'input_tokens', 0)
                output_tokens = getattr(usage, 'output_tokens', 0)
    except Exception as e:
        print(f"⚠️  Warning: Could not extract usage info: {e}")
    
    return input_tokens, output_tokens

def reset_cost_session():
    """Reset the cost session for a new run"""
    global cost_session
    cost_session = {
        "total_cost": 0.0,
        "api_calls": 0,
        "providers": {},
        "session_start": datetime.now(),
        "tokens_used": {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }
    }

def log_llm_success(provider, model, response_length, input_tokens=0, output_tokens=0, cost=0.0):
    """Log successful LLM API call with green checkmark and cost info"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"✅ [{timestamp}] LLM API call successful - {provider}:{model} (Response: {response_length} chars)")
    
    if input_tokens > 0 or output_tokens > 0:
        log_cost_info(provider, model, input_tokens, output_tokens, cost)

def log_llm_error(provider, model, error_type, error_message):
    """Log failed LLM API call with red cross"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"❌ [{timestamp}] LLM API call failed - {provider}:{model} ({error_type}: {error_message})")

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
            error_msg = "Please install the openai package: pip install openai"
            log_llm_error(model_provider, model_name, "ImportError", error_msg)
            raise ImportError(error_msg)
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            error_msg = "OPENAI_API_KEY environment variable not set."
            log_llm_error(model_provider, model_name, "API_KEY_ERROR", error_msg)
            raise ValueError(error_msg)
        
        try:
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            
            result = response.choices[0].message.content.strip()
            
            # Extract usage information and calculate cost
            input_tokens, output_tokens = extract_usage_from_response(response, model_provider)
            cost = calculate_cost(model_provider, model_name, input_tokens, output_tokens)
            
            # Update session tracking
            update_cost_session(model_provider, model_name, input_tokens, output_tokens, cost)
            
            log_llm_success(model_provider, model_name, len(result), input_tokens, output_tokens, cost)
            return result
        except Exception as e:
            log_llm_error(model_provider, model_name, "API_CALL_ERROR", str(e))
            raise
    elif model_provider.lower() == "anthropic":
        try:
            import anthropic
        except ImportError:
            error_msg = "Please install the anthropic package: pip install anthropic"
            log_llm_error(model_provider, model_name, "ImportError", error_msg)
            raise ImportError(error_msg)
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            error_msg = "ANTHROPIC_API_KEY environment variable not set."
            log_llm_error(model_provider, model_name, "API_KEY_ERROR", error_msg)
            raise ValueError(error_msg)
        
        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model=model_name,
                max_tokens=kwargs.get("max_tokens", 1024),
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = response.content[0].text.strip()
            
            # Extract usage information and calculate cost
            input_tokens, output_tokens = extract_usage_from_response(response, model_provider)
            cost = calculate_cost(model_provider, model_name, input_tokens, output_tokens)
            
            # Update session tracking
            update_cost_session(model_provider, model_name, input_tokens, output_tokens, cost)
            
            log_llm_success(model_provider, model_name, len(result), input_tokens, output_tokens, cost)
            return result
        except Exception as e:
            log_llm_error(model_provider, model_name, "API_CALL_ERROR", str(e))
            raise
    else:
        error_msg = f"Unsupported model provider: {model_provider}"
        log_llm_error(model_provider, model_name, "UNSUPPORTED_PROVIDER", error_msg)
        raise ValueError(error_msg)

import json
import sys
import os
import traceback
from datetime import datetime
from typing import List
from pathlib import Path
from pydantic import BaseModel, Field

# Add the parent directory to Python path for direct execution
if __name__ == "__main__":
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up 4 levels to get to the parent of worldmodel directory
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
    sys.path.insert(0, parent_dir)

from worldmodel.backend.llm.llm import call_llm_api

def log_error(error_type, error_message, details=None, exception=None):
    """
    Enhanced error logging function for terminal output with red cross emoji
    
    Args:
        error_type (str): Type of error (e.g., "JSON_PARSE_ERROR", "API_ERROR")
        error_message (str): Human-readable error message
        details (str, optional): Additional details about the error
        exception (Exception, optional): The original exception object for full traceback
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n{'='*60}")
    print(f"❌ ERROR [{error_type}] - {timestamp}")
    print(f"{'='*60}")
    print(f"Message: {error_message}")
    
    if details:
        print(f"Details: {details}")
    
    if exception:
        print(f"Exception Type: {type(exception).__name__}")
        print(f"Exception Message: {str(exception)}")
        print(f"\nFull Traceback:")
        traceback.print_exc()
    
    print(f"{'='*60}\n")

def log_success(message, details=None):
    """
    Success logging function with green checkmark emoji
    
    Args:
        message (str): Success message
        details (str, optional): Additional details about the success
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n{'='*60}")
    print(f"✅ SUCCESS - {timestamp}")
    print(f"{'='*60}")
    print(f"Message: {message}")
    
    if details:
        print(f"Details: {details}")
    
    print(f"{'='*60}\n")

def save_actors_to_json(actors_list: 'ActorList', model_provider: str, model_name: str, num_actors: int):
    """
    Save the ActorList to a JSON file in the init_logs folder with date-based subfolder structure
    
    Args:
        actors_list (ActorList): The validated ActorList object
        model_provider (str): The LLM provider used
        model_name (str): The model name used
        num_actors (int): Number of actors requested
    
    Returns:
        str: Path to the saved file if successful, None if failed
    """
    try:
        # Create the base init_logs directory path
        script_dir = Path(__file__).parent
        backend_dir = script_dir.parent.parent  # Go up to worldmodel/backend
        base_logs_dir = backend_dir / "init_logs"
        
        # Create the base directory if it doesn't exist
        base_logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create date-based subfolder with running integer
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Find the next available run number for today
        run_number = 1
        while True:
            subfolder_name = f"run_{current_date}_{run_number}"
            subfolder_path = base_logs_dir / subfolder_name
            
            if not subfolder_path.exists():
                # Create the subfolder
                subfolder_path.mkdir(parents=True, exist_ok=True)
                break
            
            run_number += 1
        
        # Create the filename
        filename = "Features_level_0.json"
        filepath = subfolder_path / filename
        
        # Prepare the data to save with metadata
        output_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "run_folder": subfolder_name,
                "model_provider": model_provider,
                "model_name": model_name,
                "num_actors_requested": num_actors,
                "num_actors_generated": actors_list.total_count,
                "script_version": "1.0.0",
                "generation_method": "LLM-based"
            },
            "actors": [actor.model_dump() for actor in actors_list.actors],
            "total_count": actors_list.total_count
        }
        
        # Save to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        log_success(
            "JSON file saved successfully",
            f"File: {filepath}\nRun folder: {subfolder_name}\nProvider: {model_provider}\nModel: {model_name}\nActors: {num_actors}"
        )
        return str(filepath)
        
    except Exception as e:
        log_error(
            error_type="FILE_SAVE_ERROR",
            error_message="Failed to save actors data to JSON file",
            details=f"Target file: {filepath if 'filepath' in locals() else 'unknown'}, "
                   f"Provider: {model_provider}, Model: {model_name}, "
                   f"Actors: {num_actors}",
            exception=e
        )
        return None

class Actor(BaseModel):
    """Represents a single actor in the world model"""
    name: str = Field(..., description="The name of the actor (country, company, organization, etc.)")
    description: str = Field(..., description="A short description of the actor's role and influence")
    type: str = Field(..., description="The type of actor (country, company, organization, individual, etc.)")
    influence_score: int = Field(..., ge=1, le=100, description="Influence score from 1-100 based on global impact")

class ActorList(BaseModel):
    """Container for a list of actors"""
    actors: List[Actor] = Field(..., description="List of the most influential actors in the world")
    total_count: int = Field(..., description="Total number of actors in the list")

def get_worldmodel_actors_via_llm(model_provider="anthropic", model_name="claude-3-5-sonnet-latest", num_actors=50, _retry_count=0):
    """
    Calls an LLM to generate a JSON listing the most influential actors in a dynamic world model.
    
    The function focuses on finding the most powerful and influential actors that shape global dynamics,
    including countries, multinational companies, international organizations, and key individuals.

    Args:
        model_provider (str): The LLM provider to use. Options: "anthropic", "openai". Default: "anthropic"
        model_name (str): The model name to use. Examples:
            - Anthropic: "claude-3-5-sonnet-latest", "claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3-opus-20240229"
            - OpenAI: "gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"
            Default: "claude-3-5-sonnet-latest"
        num_actors (int): The number of most influential actors to return. Default: 50
        _retry_count (int): Internal parameter for retry logic. Do not use directly.

    How to run from command line:
        # From the parent directory (58_Worldmodel):
        cd 58_Worldmodel
        source venv/bin/activate
        python -c "from worldmodel.backend.routes.1_initialization_route.actors_init import get_worldmodel_actors_via_llm; get_worldmodel_actors_via_llm()"
        
        # With different providers/models/counts:
        python -c "from worldmodel.backend.routes.1_initialization_route.actors_init import get_worldmodel_actors_via_llm; get_worldmodel_actors_via_llm('anthropic', 'claude-3-opus-20240229', 25)"
        python -c "from worldmodel.backend.routes.1_initialization_route.actors_init import get_worldmodel_actors_via_llm; get_worldmodel_actors_via_llm('openai', 'gpt-4', 100)"
        
        # Or run the file directly from the worldmodel directory:
        cd worldmodel
        python backend/routes/1_initialization_route/actors_init.py
        
        # With arguments for direct execution:
        python backend/routes/1_initialization_route/actors_init.py anthropic claude-3-5-sonnet-latest 25
        python backend/routes/1_initialization_route/actors_init.py openai gpt-4 100

    Requirements:
        - For Anthropic: You must have an Anthropic API key set in your environment as ANTHROPIC_API_KEY
        - For OpenAI: You must have an OpenAI API key set in your environment as OPENAI_API_KEY
        - The corresponding Python package must be installed ('anthropic' or 'openai')
        - Pydantic package for data validation (included in requirements.txt)

    Returns:
        ActorList: A Pydantic model containing the list of most influential actors with their details
    
    Output:
        - Successful results are automatically saved to: worldmodel/backend/init_logs/Features_level_0.json
        - The JSON file includes metadata (timestamp, model info, etc.) and the complete actor list
        - File is created with UTF-8 encoding and proper JSON formatting
    
    Error Handling:
        - Automatically retries with fewer actors if the LLM response is truncated due to token limits
        - Provides helpful error messages for common JSON parsing issues
        - Includes suggestions for manual retry with different parameters
        - File saving errors are logged but don't prevent function completion
    """
    
    system_context = (
        "You are an expert in geopolitics, international relations, and global power dynamics. "
        "Your task is to identify and rank the most influential actors that shape our world today. "
        "These actors should be the ones with the greatest impact on global economics, politics, "
        "technology, culture, and society. Focus on entities that have the power to influence "
        "international relations, global markets, and major world events.\n\n"
        
        "Return ONLY a valid JSON object with the following structure:\n"
        "{\n"
        '  "actors": [\n'
        '    {\n'
        '      "name": "Actor Name",\n'
        '      "description": "Brief description of their influence and role",\n'
        '      "type": "country|company|organization|individual|alliance",\n'
        '      "influence_score": 1-100 (integer)\n'
        '    }\n'
        '  ],\n'
        '  "total_count": number_of_actors\n'
        "}\n\n"
        "Do not include any explanation or text outside the JSON.\n\n"
    )

    user_context = (
        f"Generate a list of the {num_actors} most influential actors in the world today. "
        "These should be the entities that have the greatest power to shape global dynamics. "
        "Consider the following categories and prioritize the most impactful:\n\n"
        
        "**Countries**: Major world powers, economic superpowers, regional hegemons\n"
        "**Companies**: Multinational corporations, tech giants, financial institutions, energy companies\n"
        "**Organizations**: International bodies (UN, IMF, WTO), military alliances (NATO), economic blocs (EU, G7, G20)\n"
        "**Individuals**: World leaders, tech moguls, financial leaders, influential figures\n"
        "**Alliances**: Political, economic, or military partnerships\n\n"
        
        "For each actor, provide:\n"
        "- **name**: The official name of the actor\n"
        "- **description**: A concise explanation of their influence and global impact\n"
        "- **type**: One of: country, company, organization, individual, alliance\n"
        "- **influence_score**: A score from 1-100 based on their global influence (100 = maximum global impact)\n\n"
        
        "Rank them by influence score (highest first). Consider factors like:\n"
        "- Economic power and market capitalization\n"
        "- Political influence and diplomatic reach\n"
        "- Military capabilities and strategic importance\n"
        "- Technological innovation and control\n"
        "- Cultural and social influence\n"
        "- Resource control and energy influence\n"
        "- Population and demographic impact\n\n"
        
        f"Return exactly {num_actors} actors in the JSON format specified above."
    )

    # Combine system and user contexts into a single prompt
    full_prompt = system_context + user_context

    try:
        print(f"🔄 Using {model_provider} with model: {model_name}")
        print(f"📊 Requesting {num_actors} most influential actors...")
        
        # Call the abstracted LLM API
        response = call_llm_api(
            prompt=full_prompt,
            model_provider=model_provider,
            model_name=model_name,
            max_tokens=4096,  # Increased significantly for 50 actors with descriptions
            temperature=0.2   # Lower temperature for more consistent output
        )
        
        # Try to parse the JSON and validate with Pydantic
        try:
            raw_data = json.loads(response)
            actors_list = ActorList(**raw_data)
            
            # Pretty print the validated data with success logging
            log_success(
                f"Successfully generated {actors_list.total_count} influential actors",
                f"Provider: {model_provider}\nModel: {model_name}\nActors requested: {num_actors}\nActors generated: {actors_list.total_count}"
            )
            
            print("=" * 80)
            for i, actor in enumerate(actors_list.actors, 1):
                print(f"✅ {i:2d}. {actor.name} ({actor.type})")
                print(f"    📊 Influence Score: {actor.influence_score}/100")
                print(f"    📝 Description: {actor.description}")
                print()
            
            # Save the results to JSON file
            save_actors_to_json(actors_list, model_provider, model_name, num_actors)
            
            
            return actors_list
            
        except json.JSONDecodeError as e:
            # Check if the JSON appears to be truncated
            if "Unterminated string" in str(e) or "Expecting ',' delimiter" in str(e):
                log_error(
                    error_type="JSON_TRUNCATION_ERROR",
                    error_message="LLM response appears to be truncated due to token limit exceeded",
                    details=f"Requested {num_actors} actors with {model_provider}:{model_name}. "
                           f"Response length: {len(response)} characters. "
                           f"This usually means the response exceeded the max_tokens limit.",
                    exception=e
                )
                
                # Auto-retry with fewer actors if we haven't already retried
                if _retry_count == 0 and num_actors > 25:
                    retry_actors = max(25, num_actors // 2)
                    print(f"🔄 Auto-retrying with {retry_actors} actors instead of {num_actors}...")
                    return get_worldmodel_actors_via_llm(
                        model_provider=model_provider,
                        model_name=model_name,
                        num_actors=retry_actors,
                        _retry_count=1
                    )
                else:
                    print(f"💡 Suggestions to fix this:")
                    print(f"  1. Reduce number of actors: currently {num_actors}")
                    print(f"  2. Try: python backend/routes/1_initialization_route/actors_init.py {model_provider} {model_name} 25")
                    print(f"  3. Use a model with higher token limits (e.g., Claude Opus)")
            else:
                log_error(
                    error_type="JSON_PARSE_ERROR",
                    error_message="LLM did not return valid JSON",
                    details=f"Provider: {model_provider}, Model: {model_name}, "
                           f"Actors requested: {num_actors}, Response length: {len(response)} characters",
                    exception=e
                )
            
            print("\n📄 Raw LLM output (for debugging):")
            print("-" * 50)
            print(response)
            print("-" * 50)
            return None
        except Exception as e:
            log_error(
                error_type="PYDANTIC_VALIDATION_ERROR",
                error_message="Data validation failed - LLM response doesn't match expected schema",
                details=f"Provider: {model_provider}, Model: {model_name}, "
                       f"Actors requested: {num_actors}. "
                       f"The LLM returned valid JSON but it doesn't match the expected Actor schema.",
                exception=e
            )
            print("\n📄 Raw JSON data (for debugging):")
            print("-" * 50)
            try:
                print(json.dumps(raw_data, indent=2))
            except:
                print("Could not format raw data as JSON")
                print(raw_data)
            print("-" * 50)
            return None
            
    except Exception as e:
        # Determine error type based on the exception message
        if "API key" in str(e) or "ANTHROPIC_API_KEY" in str(e) or "OPENAI_API_KEY" in str(e):
            error_type = "API_KEY_ERROR"
            error_message = f"API key not found or invalid for {model_provider}"
            details = f"Make sure you have the correct API key set. "
            if model_provider.lower() == "anthropic":
                details += "Required environment variable: ANTHROPIC_API_KEY"
            elif model_provider.lower() == "openai":
                details += "Required environment variable: OPENAI_API_KEY"
            else:
                details += f"Check the API key for {model_provider}"
        elif "quota" in str(e).lower() or "limit" in str(e).lower():
            error_type = "API_QUOTA_ERROR"
            error_message = f"API quota or rate limit exceeded for {model_provider}"
            details = f"Provider: {model_provider}, Model: {model_name}. " \
                     f"You may have exceeded your API quota or rate limit. Try again later."
        elif "connection" in str(e).lower() or "timeout" in str(e).lower():
            error_type = "API_CONNECTION_ERROR"
            error_message = f"Connection error when calling {model_provider} API"
            details = f"Provider: {model_provider}, Model: {model_name}. " \
                     f"Check your internet connection and try again."
        elif "model" in str(e).lower() and "not found" in str(e).lower():
            error_type = "MODEL_NOT_FOUND_ERROR"
            error_message = f"Model '{model_name}' not found or not available"
            details = f"Provider: {model_provider}, Model: {model_name}. " \
                     f"Check that the model name is correct and available for your API key."
        else:
            error_type = "GENERAL_API_ERROR"
            error_message = f"Unexpected error when calling {model_provider} API"
            details = f"Provider: {model_provider}, Model: {model_name}, " \
                     f"Actors requested: {num_actors}"
        
        log_error(
            error_type=error_type,
            error_message=error_message,
            details=details,
            exception=e
        )
        return None

# Allow direct execution of the script
if __name__ == "__main__":
    # Default values
    provider = "anthropic"
    model = "claude-3-5-sonnet-latest"
    num_actors = 10
    
    # Parse command line arguments with better error handling
    if len(sys.argv) > 1:
        provider = sys.argv[1]
    if len(sys.argv) > 2:
        model = sys.argv[2]
    if len(sys.argv) > 3:
        try:
            num_actors = int(sys.argv[3])
            if num_actors < 1 or num_actors > 200:
                print(f"⚠️ Warning: Number of actors should be between 1-200. Got {num_actors}, using default: 50")
                num_actors = 50
        except ValueError:
            log_error(
                error_type="ARGUMENT_ERROR",
                error_message=f"Invalid number of actors argument: '{sys.argv[3]}'",
                details=f"Expected an integer between 1-200. Using default: {num_actors}"
            )
    
    print(f"🌍 Running World Model Actor Analysis")
    print(f"🔧 Provider: {provider}")
    print(f"🤖 Model: {model}")
    print(f"📊 Number of actors: {num_actors}")
    print("=" * 50)
    
    try:
        result = get_worldmodel_actors_via_llm(provider, model, num_actors)
        
        if result:
            log_success(
                f"Analysis complete! Generated {result.total_count} influential actors",
                f"Provider: {provider}\nModel: {model}\nActors: {result.total_count}"
            )
            print("Use the returned ActorList object for further processing.")
        else:
            print("\n❌ Analysis failed. See error details above.")
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Analysis interrupted by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        log_error(
            error_type="UNEXPECTED_ERROR",
            error_message="Unexpected error during analysis execution",
            details=f"Provider: {provider}, Model: {model}, Actors: {num_actors}",
            exception=e
        )
        sys.exit(1)

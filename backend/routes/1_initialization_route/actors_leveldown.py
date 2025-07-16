import json
import sys
import os
import traceback
from datetime import datetime
from typing import List, Dict, Any
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
    Enhanced error logging function for terminal output
    
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

class SubActor(BaseModel):
    """Represents a sub-actor within a main actor"""
    name: str = Field(..., description="The name of the sub-actor")
    description: str = Field(..., description="A detailed description of the sub-actor's role and influence")
    type: str = Field(..., description="The type of sub-actor (e.g., administration, company, movement, individual)")
    influence_score: int = Field(..., ge=1, le=100, description="Influence score from 1-100 within the parent actor's context")
    parent_actor: str = Field(..., description="The name of the parent actor this sub-actor belongs to")

class SubActorList(BaseModel):
    """Container for a list of sub-actors for a specific parent actor"""
    sub_actors: List[SubActor] = Field(..., description="List of sub-actors within the parent actor")
    total_count: int = Field(..., description="Total number of sub-actors in the list")
    parent_actor: str = Field(..., description="The parent actor these sub-actors belong to")

class EnhancedActor(BaseModel):
    """Enhanced actor model that includes sub-actors"""
    name: str = Field(..., description="The name of the actor")
    description: str = Field(..., description="A short description of the actor's role and influence")
    type: str = Field(..., description="The type of actor")
    influence_score: int = Field(..., ge=1, le=100, description="Influence score from 1-100")
    sub_actors: List[SubActor] = Field(default=[], description="List of sub-actors within this actor")
    sub_actors_count: int = Field(default=0, description="Number of sub-actors")

def load_features_level_0() -> Dict[str, Any]:
    """
    Load the Features_level_0.json file containing the main actors from the most recent run folder
    
    Returns:
        Dict[str, Any]: The loaded JSON data
    """
    try:
        # Get the path to the init_logs directory
        script_dir = Path(__file__).parent
        backend_dir = script_dir.parent.parent  # Go up to worldmodel/backend
        init_logs_dir = backend_dir / "init_logs"
        
        if not init_logs_dir.exists():
            raise FileNotFoundError(f"init_logs directory not found at: {init_logs_dir}")
        
        # Find the most recent run folder
        run_folders = [d for d in init_logs_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
        
        if not run_folders:
            raise FileNotFoundError(f"No run folders found in: {init_logs_dir}")
        
        # Sort folders by creation time (most recent first)
        run_folders.sort(key=lambda x: x.stat().st_ctime, reverse=True)
        most_recent_folder = run_folders[0]
        
        # Look for Features_level_0.json in the most recent folder
        filepath = most_recent_folder / "Features_level_0.json"
        
        if not filepath.exists():
            raise FileNotFoundError(f"Features_level_0.json not found in most recent run folder: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"📄 Successfully loaded Features_level_0.json from {most_recent_folder.name}")
        print(f"📊 Found {len(data.get('actors', []))} main actors")
        return data
        
    except Exception as e:
        log_error(
            error_type="FILE_LOAD_ERROR",
            error_message="Failed to load Features_level_0.json from run folders",
            details=f"Target directory: {init_logs_dir if 'init_logs_dir' in locals() else 'unknown'}",
            exception=e
        )
        raise

def generate_subactors_for_actor(actor_data: Dict[str, Any], model_provider: str, model_name: str, num_subactors: int = 8) -> SubActorList:
    """
    
    Generate sub-actors for a specific main actor using LLM
    
    Args:
        actor_data (Dict[str, Any]): The main actor data
        model_provider (str): The LLM provider to use
        model_name (str): The model name to use
        num_subactors (int): Number of sub-actors to generate
        
    Returns:
        SubActorList: Validated list of sub-actors
    """
    
    actor_name = actor_data["name"]
    actor_description = actor_data["description"]
    actor_type = actor_data["type"]
    
    # Create context-aware prompts based on actor type
    system_context = (
        "You are an expert analyst specializing in organizational structures, hierarchies, and influence networks. "
        "Your task is to identify and analyze the most influential sub-entities within a given main actor. "
        "These sub-actors should be the key components that collectively make up the main actor's influence and power.\n\n"
        
        "Return ONLY a valid JSON object with the following structure:\n"
        "{\n"
        '  "sub_actors": [\n'
        '    {\n'
        '      "name": "Sub-Actor Name",\n'
        '      "description": "Detailed description of their role and influence within the parent actor",\n'
        '      "type": "administration|company|movement|individual|department|institution|faction|other",\n'
        '      "influence_score": 1-100 (integer),\n'
        '      "parent_actor": "' + actor_name + '"\n'
        '    }\n'
        '  ],\n'
        '  "total_count": number_of_sub_actors,\n'
        '  "parent_actor": "' + actor_name + '"\n'
        "}\n\n"
        "Do not include any explanation or text outside the JSON.\n\n"
    )
    
    # Generate type-specific suggestions
    type_suggestions = {
        "country": "government branches, military divisions, major political parties, key ministries, intelligence agencies, economic sectors, social movements, major companies, influential individuals, regional governments",
        "company": "business divisions, subsidiaries, key executives, product lines, research departments, regional offices, major shareholders, board members, technology platforms, strategic partnerships",
        "organization": "departments, committees, member organizations, leadership bodies, regional offices, working groups, specialized agencies, key officials, advisory boards, operational units",
        "alliance": "member states, secretariat, military commands, economic bodies, political institutions, decision-making bodies, regional groups, specialized agencies, key leaders, operational divisions",
        "individual": "personal ventures, foundations, investment firms, social networks, political affiliations, business interests, family members, key advisors, media platforms, influence networks"
    }
    
    suggestions = type_suggestions.get(actor_type.lower(), "key departments, leadership, subsidiaries, affiliated organizations, influential members, operational divisions, strategic units, advisory bodies")
    
    user_context = (
        f"Analyze the following main actor and generate {num_subactors} most influential sub-actors within it:\n\n"
        f"**Main Actor**: {actor_name}\n"
        f"**Type**: {actor_type}\n"
        f"**Description**: {actor_description}\n\n"
        
        f"Generate the {num_subactors} most influential sub-actors that make up or significantly influence this main actor. "
        f"Consider entities like: {suggestions}\n\n"
        
        "For each sub-actor, provide:\n"
        "- **name**: The specific name of the sub-actor\n"
        "- **description**: A detailed explanation of their role, influence, and importance within the parent actor\n"
        "- **type**: The category of sub-actor (be specific - e.g., 'government_ministry', 'ceo', 'political_party', etc.)\n"
        "- **influence_score**: A score from 1-100 based on their influence within the parent actor's context\n"
        f"- **parent_actor**: Must be exactly '{actor_name}'\n\n"
        
        "Rank them by influence score within the parent actor's context (highest first). "
        "Focus on the most powerful and influential components that shape the main actor's behavior and decisions.\n\n"
        
        f"Return exactly {num_subactors} sub-actors in the JSON format specified above."
    )
    
    full_prompt = system_context + user_context
    
    try:
        print(f"🔄 Generating sub-actors for: {actor_name}")
        
        # Call the LLM API
        response = call_llm_api(
            prompt=full_prompt,
            model_provider=model_provider,
            model_name=model_name,
            max_tokens=3000,
            temperature=0.3
        )
        
        # Parse and validate the response
        try:
            raw_data = json.loads(response)
            sub_actors_list = SubActorList(**raw_data)
            
            print(f"✅ Generated {sub_actors_list.total_count} sub-actors for {actor_name}")
            return sub_actors_list
            
        except json.JSONDecodeError as e:
            log_error(
                error_type="JSON_PARSE_ERROR",
                error_message=f"Failed to parse JSON response for {actor_name}",
                details=f"Response length: {len(response)} characters",
                exception=e
            )
            print(f"📄 Raw response for {actor_name}:")
            print("-" * 50)
            print(response)
            print("-" * 50)
            raise
            
        except Exception as e:
            log_error(
                error_type="VALIDATION_ERROR",
                error_message=f"Data validation failed for {actor_name}",
                details=f"LLM returned valid JSON but it doesn't match the expected schema",
                exception=e
            )
            raise
            
    except Exception as e:
        log_error(
            error_type="SUBACTOR_GENERATION_ERROR",
            error_message=f"Failed to generate sub-actors for {actor_name}",
            details=f"Provider: {model_provider}, Model: {model_name}",
            exception=e
        )
        raise

def save_enhanced_actors_to_json(enhanced_actors: List[EnhancedActor], original_metadata: Dict[str, Any], 
                                model_provider: str, model_name: str, total_subactors: int):
    """
    Save the enhanced actors with sub-actors to a new JSON file in the same run folder as the source data
    
    Args:
        enhanced_actors (List[EnhancedActor]): List of actors with their sub-actors
        original_metadata (Dict[str, Any]): Original metadata from round 0
        model_provider (str): LLM provider used
        model_name (str): Model name used
        total_subactors (int): Total number of sub-actors generated
    """
    try:
        # Get the path to the init_logs directory
        script_dir = Path(__file__).parent
        backend_dir = script_dir.parent.parent  # Go up to worldmodel/backend
        init_logs_dir = backend_dir / "init_logs"
        
        # Find the most recent run folder (same as used in load_features_round_0)
        run_folders = [d for d in init_logs_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
        
        if not run_folders:
            raise FileNotFoundError(f"No run folders found in: {init_logs_dir}")
        
        # Sort folders by creation time (most recent first)
        run_folders.sort(key=lambda x: x.stat().st_ctime, reverse=True)
        most_recent_folder = run_folders[0]
        
        # Create the filename for level 1 in the same run folder
        filename = "Features_level_1.json"
        filepath = most_recent_folder / filename
        
        # Calculate statistics
        total_main_actors = len(enhanced_actors)
        actors_with_subactors = sum(1 for actor in enhanced_actors if actor.sub_actors_count > 0)
        avg_subactors_per_actor = total_subactors / total_main_actors if total_main_actors > 0 else 0
        
        # Prepare the enhanced data structure
        output_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "run_folder": most_recent_folder.name,
                "model_provider": model_provider,
                "model_name": model_name,
                "script_version": "1.0.0",
                "level": 1,
                "parent_file": "Features_level_0.json",
                "original_metadata": original_metadata,
                "generation_stats": {
                    "total_main_actors": total_main_actors,
                    "total_subactors": total_subactors,
                    "actors_with_subactors": actors_with_subactors,
                    "avg_subactors_per_actor": round(avg_subactors_per_actor, 2)
                }
            },
            "actors": [actor.model_dump() for actor in enhanced_actors],
            "total_main_actors": total_main_actors,
            "total_subactors": total_subactors,
            "level": 1
        }
        
        # Save to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Enhanced JSON saved successfully: {filepath}")
        print(f"📁 Run folder: {most_recent_folder.name}")
        return str(filepath)
        
    except Exception as e:
        log_error(
            error_type="FILE_SAVE_ERROR",
            error_message="Failed to save enhanced actors data to JSON file",
            details=f"Target file: {filepath if 'filepath' in locals() else 'unknown'}",
            exception=e
        )
        return None

def generate_actor_leveldown(model_provider="anthropic", model_name="claude-3-5-sonnet-latest", 
                           num_subactors_per_actor=8, skip_on_error=True):
    """
    Generate sub-actors for all main actors from Features_round_0.json
    
    Args:
        model_provider (str): The LLM provider to use
        model_name (str): The model name to use
        num_subactors_per_actor (int): Number of sub-actors to generate per main actor
        skip_on_error (bool): Whether to skip actors that fail instead of stopping entirely
    
    Returns:
        List[EnhancedActor]: List of enhanced actors with their sub-actors
    """
    
    print(f"🌍 Starting Actor Level-Down Analysis")
    print(f"Provider: {model_provider}")
    print(f"Model: {model_name}")
    print(f"Sub-actors per actor: {num_subactors_per_actor}")
    print(f"Skip on error: {skip_on_error}")
    print("=" * 60)
    
    # Load the original data
    try:
        original_data = load_features_level_0()
        main_actors = original_data["actors"]
        original_metadata = original_data["metadata"]
        
        print(f"📊 Processing {len(main_actors)} main actors...")
        
    except Exception as e:
        print(f"❌ Failed to load original data: {e}")
        return None
    
    # Process each main actor
    enhanced_actors = []
    total_subactors = 0
    successful_actors = 0
    failed_actors = 0
    
    for i, actor_data in enumerate(main_actors, 1):
        actor_name = actor_data["name"]
        
        try:
            print(f"\n[{i}/{len(main_actors)}] Processing: {actor_name}")
            
            # Generate sub-actors for this main actor
            sub_actors_list = generate_subactors_for_actor(
                actor_data, model_provider, model_name, num_subactors_per_actor
            )
            
            # Create enhanced actor
            enhanced_actor = EnhancedActor(
                name=actor_data["name"],
                description=actor_data["description"],
                type=actor_data["type"],
                influence_score=actor_data["influence_score"],
                sub_actors=sub_actors_list.sub_actors,
                sub_actors_count=sub_actors_list.total_count
            )
            
            enhanced_actors.append(enhanced_actor)
            total_subactors += sub_actors_list.total_count
            successful_actors += 1
            
            # Print sub-actors for this main actor
            print(f"    📋 Sub-actors for {actor_name}:")
            for j, sub_actor in enumerate(sub_actors_list.sub_actors, 1):
                print(f"      {j:2d}. {sub_actor.name} ({sub_actor.type}) - Score: {sub_actor.influence_score}")
            
        except Exception as e:
            failed_actors += 1
            
            if skip_on_error:
                print(f"⚠️  Skipping {actor_name} due to error: {e}")
                # Add the actor without sub-actors
                enhanced_actor = EnhancedActor(
                    name=actor_data["name"],
                    description=actor_data["description"],
                    type=actor_data["type"],
                    influence_score=actor_data["influence_score"],
                    sub_actors=[],
                    sub_actors_count=0
                )
                enhanced_actors.append(enhanced_actor)
            else:
                print(f"❌ Failed to process {actor_name}: {e}")
                return None
    
    # Print final statistics
    print(f"\n{'='*60}")
    print(f"🎯 LEVEL-DOWN ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"📊 Statistics:")
    print(f"   • Total main actors: {len(main_actors)}")
    print(f"   • Successfully processed: {successful_actors}")
    print(f"   • Failed to process: {failed_actors}")
    print(f"   • Total sub-actors generated: {total_subactors}")
    print(f"   • Average sub-actors per main actor: {total_subactors / len(main_actors):.2f}")
    print(f"   • Actors with sub-actors: {sum(1 for actor in enhanced_actors if actor.sub_actors_count > 0)}")
    
    # Save the enhanced data
    try:
        save_enhanced_actors_to_json(enhanced_actors, original_metadata, model_provider, model_name, total_subactors)
        print(f"✅ Enhanced data saved to Features_level_1.json")
    except Exception as e:
        print(f"⚠️  Failed to save enhanced data: {e}")
    
    return enhanced_actors

# Allow direct execution of the script
if __name__ == "__main__":
    # Default values
    provider = "anthropic"
    model = "claude-3-5-sonnet-latest"
    num_subactors = 8
    skip_errors = True
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        provider = sys.argv[1]
    if len(sys.argv) > 2:
        model = sys.argv[2]
    if len(sys.argv) > 3:
        try:
            num_subactors = int(sys.argv[3])
            if num_subactors < 1 or num_subactors > 20:
                print(f"⚠️ Warning: Number of sub-actors should be between 1-20. Got {num_subactors}, using 8")
                num_subactors = 8
        except ValueError:
            print(f"⚠️ Warning: Invalid sub-actors argument: '{sys.argv[3]}', using default: 8")
    if len(sys.argv) > 4:
        skip_errors = sys.argv[4].lower() in ['true', '1', 'yes', 'on']
    
    try:
        result = generate_actor_leveldown(provider, model, num_subactors, skip_errors)
        
        if result:
            print(f"\n🎉 Level-down analysis completed successfully!")
            print(f"📁 Results saved to Features_level_1.json")
        else:
            print(f"\n❌ Level-down analysis failed.")
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Analysis interrupted by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        log_error(
            error_type="UNEXPECTED_ERROR",
            error_message="Unexpected error during level-down analysis",
            details=f"Provider: {provider}, Model: {model}, Sub-actors: {num_subactors}",
            exception=e
        )
        sys.exit(1)

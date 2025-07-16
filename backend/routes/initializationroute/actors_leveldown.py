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
from worldmodel.backend.llm.llm import get_cost_session
from worldmodel.backend.llm.llm import reset_cost_session
from worldmodel.backend.llm.llm import print_cost_summary
from worldmodel.backend.routes.initializationroute.prompts import generate_leveldown_prompts

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
    parent_actor: str = Field(..., description="The name of the parent actor this sub-actor belongs to")
    sub_actors: List['SubActor'] = Field(default=[], description="List of nested sub-actors within this sub-actor")
    sub_actors_count: int = Field(default=0, description="Number of nested sub-actors")

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
    sub_actors: List[SubActor] = Field(default=[], description="List of sub-actors within this actor")
    sub_actors_count: int = Field(default=0, description="Number of sub-actors")

# Resolve forward reference for recursive SubActor model
SubActor.model_rebuild()

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

def generate_subactors_for_actor(actor_data: Dict[str, Any], model_provider: str, model_name: str, num_subactors: int = 8, current_level: int = 1) -> SubActorList:
    """
    Generate sub-actors for a specific main actor using LLM with level-specific prompts
    
    Args:
        actor_data (Dict[str, Any]): The main actor data
        model_provider (str): The LLM provider to use
        model_name (str): The model name to use
        num_subactors (int): Number of sub-actors to generate
        current_level (int): Current level being generated (1=countries, 2=companies, 3=people, 4=movements)
        
    Returns:
        SubActorList: Validated list of sub-actors
    """
    
    actor_name = actor_data["name"]
    actor_description = actor_data["description"]
    actor_type = actor_data["type"]
    
    # Generate prompts using the centralized prompts module
    system_context, user_context = generate_leveldown_prompts(
        actor_name, actor_description, actor_type, num_subactors, current_level
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
                                model_provider: str, model_name: str, total_subactors: int, level: int = 1):
    """
    Save the enhanced actors with sub-actors to a new JSON file in the same run folder as the source data
    
    Args:
        enhanced_actors (List[EnhancedActor]): List of actors with their sub-actors
        original_metadata (Dict[str, Any]): Original metadata from round 0
        model_provider (str): LLM provider used
        model_name (str): Model name used
        total_subactors (int): Total number of sub-actors generated
        level (int): Level number for the output file (default: 1)
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
        
        # Create the filename for the specified level in the same run folder
        filename = f"Features_level_{level}.json"
        filepath = most_recent_folder / filename
        
        # Calculate statistics
        total_main_actors = len(enhanced_actors)
        actors_with_subactors = sum(1 for actor in enhanced_actors if actor.sub_actors_count > 0)
        avg_subactors_per_actor = total_subactors / total_main_actors if total_main_actors > 0 else 0
        
        # Get current cost session data
        cost_data = get_cost_session()
        
        # Prepare the enhanced data structure
        output_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "run_folder": most_recent_folder.name,
                "model_provider": model_provider,
                "model_name": model_name,
                "script_version": "1.0.0",
                "level": level,
                "parent_file": f"Features_level_{level-1}.json",
                "original_metadata": original_metadata,
                "generation_stats": {
                    "total_main_actors": total_main_actors,
                    "total_subactors": total_subactors,
                    "actors_with_subactors": actors_with_subactors,
                    "avg_subactors_per_actor": round(avg_subactors_per_actor, 2)
                },
                "cost_tracking": cost_data
            },
            "actors": [actor.model_dump() for actor in enhanced_actors],
            "total_main_actors": total_main_actors,
            "total_subactors": total_subactors,
            "level": level
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

def generate_actor_leveldown(model_provider: str = "anthropic", 
                             model_name: str = "claude-3-5-sonnet-latest", 
                             num_subactors_per_actor: int = 8, 
                             skip_on_error: bool = True,
                             target_level: int = 1):
    """
    Generate sub-actors down to *target_level* depth for the latest run folder.

    If the requested level JSON already exists it will be reused.  Missing
    intermediate levels are generated automatically.  The routine aborts early if
    a requested level is impossible because parent actors have no sub-actors.

    Args:
        model_provider: LLM provider to use ("anthropic" or "openai", …).
        model_name: Concrete model name.
        num_subactors_per_actor: Number of sub-actors to generate for each
            parent actor at the current level.
        skip_on_error: Skip problematic actors instead of aborting the whole
            run.
        target_level: Depth level to generate (1 = first sub-actor layer,
            2 = sub-sub-actors, …).
    Returns:
        Path to the last generated level JSON or None if nothing was done.
    """
    
    print(f"🌍 Starting Actor Level-Down Analysis")
    print(f"Provider: {model_provider}")
    print(f"Model: {model_name}")
    print(f"Sub-actors per actor: {num_subactors_per_actor}")
    print(f"Target level: {target_level}")
    print(f"Skip on error: {skip_on_error}")
    print("=" * 60)
    
    # Reset cost session once at the very beginning
    reset_cost_session()
    
    # Determine most recent run folder and deepest existing level
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent.parent
    init_logs_dir = backend_dir / "init_logs"
    run_folders = [d for d in init_logs_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
    if not run_folders:
        print("❌ No run folders found – please execute level 0 generation first.")
        return None

    run_folders.sort(key=lambda x: x.stat().st_ctime, reverse=True)
    run_folder = run_folders[0]

    # Helper to load a level JSON
    def _load_level(level:int):
        fp = run_folder / f"Features_level_{level}.json"
        if not fp.exists():
            return None, fp
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f), fp

    # Discover deepest existing file
    deepest_existing = 0
    while True:
        data,_ = _load_level(deepest_existing)
        if data is None:
            break
        deepest_existing += 1
    deepest_existing -= 1  # step back to last existing

    if target_level <= deepest_existing:
        print(f"✅ Requested level {target_level} already exists – nothing to do.")
        return run_folder / f"Features_level_{target_level}.json"

    if deepest_existing < 0:
        print("❌ Level 0 data not found – run initialization first.")
        return None

    current_level = deepest_existing

    while current_level < target_level:
        parent_data, parent_fp = _load_level(current_level)
        if parent_data is None:
            print(f"❌ Cannot generate level {current_level+1} because parent level file is missing.")
            break

        parent_actors = parent_data.get("actors", [])

        # For level 0->1: expand main actors without sub-actors
        # For level 1->2: expand sub-actors from level 1
        # For level 2->3: expand sub-actors from level 2, etc.
        if current_level == 0:
            # Level 0->1: expand main actors without sub-actors
            expandable = [a for a in parent_actors if not a.get("sub_actors")]
        else:
            # Level 1->2, 2->3, etc.: expand sub-actors from previous level
            expandable = []
            for actor in parent_actors:
                if actor.get("sub_actors"):
                    expandable.extend(actor["sub_actors"])
                    
        if not expandable:
            print(f"⚠️  No expandable actors found in level {current_level}. Stopping generation.")
            break

        print(f"\n{'='*60}\n🔽 Generating level {current_level+1} from parent file {parent_fp.name}\n{'='*60}")

        # Re-use existing generation code for one layer
        # Load original_metadata only once (from level 0)
        if current_level == 0:
            original_metadata = parent_data.get("metadata", {})
        else:
            # For level 1+, try to get original_metadata from the parent data
            original_metadata = parent_data.get("metadata", {}).get("original_metadata", parent_data.get("metadata", {}))

        # Process expandable actors (main actors for level 0->1, sub-actors for level 1->2+)
        total_subactors = 0
        enhanced_actors = []
        successful_actors = failed_actors = 0

        if current_level == 0:
            # Level 0->1: Process main actors
            for actor_data in parent_actors:
                actor_name = actor_data["name"]
                if actor_data.get("sub_actors"):
                    # Already has sub-actors – keep them
                    enhanced_actors.append(EnhancedActor(**actor_data))
                    continue

                try:
                    sub_list = generate_subactors_for_actor(actor_data, model_provider, model_name, num_subactors_per_actor, current_level + 1)
                    enhanced_actors.append(EnhancedActor(
                        name=actor_data["name"],
                        description=actor_data["description"],
                        type=actor_data["type"],
                        sub_actors=sub_list.sub_actors,
                        sub_actors_count=sub_list.total_count,
                    ))
                    total_subactors += sub_list.total_count
                    successful_actors += 1
                except Exception as e:
                    failed_actors += 1
                    if skip_on_error:
                        enhanced_actors.append(EnhancedActor(**actor_data))
                    else:
                        raise
        else:
            # Level 1->2+: Process sub-actors from previous level
            for main_actor in parent_actors:
                updated_sub_actors = []
                for sub_actor in main_actor.get("sub_actors", []):
                    if sub_actor.get("sub_actors"):
                        # Sub-actor already has sub-actors – keep them
                        updated_sub_actors.append(SubActor(**sub_actor))
                        continue
                    
                    try:
                        sub_list = generate_subactors_for_actor(sub_actor, model_provider, model_name, num_subactors_per_actor, current_level + 1)
                        updated_sub_actor = SubActor(
                            name=sub_actor["name"],
                            description=sub_actor["description"],
                            type=sub_actor["type"],
                            parent_actor=sub_actor["parent_actor"],
                            sub_actors=sub_list.sub_actors,
                            sub_actors_count=sub_list.total_count
                        )
                        updated_sub_actors.append(updated_sub_actor)
                        total_subactors += sub_list.total_count
                        successful_actors += 1
                    except Exception as e:
                        failed_actors += 1
                        if skip_on_error:
                            updated_sub_actors.append(SubActor(**sub_actor))
                        else:
                            raise
                
                # Create enhanced main actor with updated sub-actors
                enhanced_actors.append(EnhancedActor(
                    name=main_actor["name"],
                    description=main_actor["description"],
                    type=main_actor["type"],
                    sub_actors=updated_sub_actors,
                    sub_actors_count=len(updated_sub_actors)
                ))

        # Save the current level file using existing helper
        save_enhanced_actors_to_json(
            enhanced_actors,
            original_metadata,
            model_provider,
            model_name,
            total_subactors,
            current_level + 1,
        )

        print_cost_summary()

        current_level += 1

    return run_folder / f"Features_level_{current_level}.json"

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
    if len(sys.argv) > 5:
        try:
            target_level = int(sys.argv[5])
            if target_level < 1:
                print("⚠️  Warning: target_level must be >=1. Using 1.")
                target_level = 1
        except ValueError:
            print(f"⚠️  Warning: Invalid target_level '{sys.argv[5]}', using 1.")
            target_level = 1
    else:
        target_level = 1
    
    try:
        result = generate_actor_leveldown(provider, model, num_subactors, skip_errors, target_level)
        
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

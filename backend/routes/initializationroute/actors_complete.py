#!/usr/bin/env python3
"""
Complete World Model Actor Generation System

This script combines both initial actor generation (Level 0) and hierarchical 
level-down generation (Levels 1-N) into one unified system. It automatically
generates all levels from 0 to the specified target depth.

Usage:
    python actors_complete.py <provider> <model> <target_depth> <level_counts> [skip_errors]

Where:
    <target_depth>   : Depth of hierarchy to generate (0–3). 0 means only top-level actors.
    <level_counts>   : Comma-separated list of FOUR integers giving the number of
                       actors/sub-actors for each level (Level 0 → Level 3).
                       Example: "5,3,5,0" generates 5 top-level actors, 3 sub-actors
                       per actor at depth-1, 5 at depth-2, and no generation at depth-3.

Examples:
    python actors_complete.py anthropic claude-3-5-sonnet-latest 3 "5,3,5,0" true
    python actors_complete.py openai gpt-4 2 100,10,5,3 false
"""

import json
import sys
import os
import traceback
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import BaseModel, Field

# Add the parent directory to Python path for direct execution
if __name__ == "__main__":
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up 4 levels to get to the parent of worldmodel directory
    parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
    sys.path.insert(0, parent_dir)

from worldmodel.backend.llm.llm import call_llm_api, get_cost_session, reset_cost_session, print_cost_summary
from worldmodel.backend.routes.initializationroute.prompts import generate_initial_actor_prompts, generate_leveldown_prompts

# Global semaphore for controlling concurrent requests
SEMAPHORE = asyncio.Semaphore(5)

# ==================== ASYNC WRAPPER FOR LLM API ====================

async def call_llm_api_async(prompt: str, model_provider: str, model_name: str, 
                            max_tokens: int = 4096, temperature: float = 0.2) -> str:
    """Async wrapper for the LLM API call"""
    async with SEMAPHORE:
        # Run the synchronous LLM API call in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: call_llm_api(
                prompt=prompt,
                model_provider=model_provider,
                model_name=model_name,
                max_tokens=max_tokens,
                temperature=temperature
            )
        )

# ==================== LOGGING FUNCTIONS ====================

def log_error(error_type, error_message, details=None, exception=None):
    """Enhanced error logging function for terminal output with red cross emoji"""
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
    """Success logging function with green checkmark emoji"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n{'='*60}")
    print(f"✅ SUCCESS - {timestamp}")
    print(f"{'='*60}")
    print(f"Message: {message}")
    
    if details:
        print(f"Details: {details}")
    
    print(f"{'='*60}\n")

def log_info(message, details=None):
    """Info logging function with blue info emoji"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n{'='*60}")
    print(f"ℹ️  INFO - {timestamp}")
    print(f"{'='*60}")
    print(f"Message: {message}")
    
    if details:
        print(f"Details: {details}")
    
    print(f"{'='*60}\n")

# ==================== DATA MODELS ====================

class Actor(BaseModel):
    """Represents a single actor in the world model"""
    name: str = Field(..., description="The name of the actor")
    description: str = Field(..., description="A short description of the actor's role and influence")
    type: str = Field(..., description="The type of actor")
    depth: int = Field(default=1, description="The depth level of the actor (1=top-level, up to 4)")

class ActorList(BaseModel):
    """Container for a list of actors"""
    actors: List[Actor] = Field(..., description="List of the most influential actors")
    total_count: int = Field(..., description="Total number of actors in the list")

class SubActor(BaseModel):
    """Represents a sub-actor within a main actor"""
    name: str = Field(..., description="The name of the sub-actor")
    description: str = Field(..., description="A detailed description of the sub-actor's role and influence")
    type: str = Field(..., description="The type of sub-actor")
    parent_actor: str = Field(..., description="The name of the parent actor")
    sub_actors: List['SubActor'] = Field(default=[], description="List of nested sub-actors")
    sub_actors_count: int = Field(default=0, description="Number of nested sub-actors")
    depth: int = Field(default=0, description="The depth level of the sub-actor (2=first sub-level, up to 4)")

class SubActorList(BaseModel):
    """Container for a list of sub-actors"""
    sub_actors: List[SubActor] = Field(..., description="List of sub-actors")
    total_count: int = Field(..., description="Total number of sub-actors")
    parent_actor: str = Field(..., description="The parent actor")

class EnhancedActor(BaseModel):
    """Enhanced actor model that includes sub-actors"""
    name: str = Field(..., description="The name of the actor")
    description: str = Field(..., description="A short description of the actor's role and influence")
    type: str = Field(..., description="The type of actor")
    sub_actors: List[SubActor] = Field(default=[], description="List of sub-actors")
    sub_actors_count: int = Field(default=0, description="Number of sub-actors")
    depth: int = Field(default=1, description="The depth level of the actor (1=top-level, up to 4)")

# Resolve forward reference for recursive SubActor model
SubActor.model_rebuild()

# ==================== FILE MANAGEMENT ====================

def get_run_folder_path() -> Path:
    """Get the path to the most recent run folder or create a new one"""
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent.parent
    base_logs_dir = backend_dir / "init_logs"
    base_logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create date-based subfolder with running integer
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Find the next available run number for today
    run_number = 1
    while True:
        subfolder_name = f"run_{current_date}_{run_number}"
        subfolder_path = base_logs_dir / subfolder_name
        
        if not subfolder_path.exists():
            subfolder_path.mkdir(parents=True, exist_ok=True)
            return subfolder_path
        
        run_number += 1

def save_level_data(data: Dict[str, Any], level: int, run_folder: Path) -> Optional[str]:
    """Save level data to JSON file"""
    try:
        filename = f"Features_level_{level}.json"
        filepath = run_folder / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        log_success(
            f"Level {level} JSON saved successfully",
            f"File: {filepath}\nRun folder: {run_folder.name}"
        )
        return str(filepath)
        
    except Exception as e:
        log_error(
            error_type="FILE_SAVE_ERROR",
            error_message=f"Failed to save level {level} data to JSON file",
            details=f"Target file: {filepath if 'filepath' in locals() else 'unknown'}",
            exception=e
        )
        return None

# ==================== LEVEL 0 GENERATION ====================

def generate_level_0_actors(model_provider: str, model_name: str, num_actors: int, 
                           run_folder: Path, _retry_count: int = 0) -> Optional[ActorList]:
    """Generate Level 0 (initial) actors"""
    
    print(f"🌍 LEVEL 0: Generating {num_actors} initial world actors")
    print(f"🔧 Provider: {model_provider}")
    print(f"🤖 Model: {model_name}")
    print("=" * 60)
    
    # Generate prompts using the centralized prompts module
    system_context, user_context = generate_initial_actor_prompts(num_actors)
    full_prompt = system_context + user_context

    try:
        print(f"🔄 Using {model_provider} with model: {model_name}")
        print(f"📊 Requesting {num_actors} most influential actors...")
        
        # Call the abstracted LLM API
        response = call_llm_api(
            prompt=full_prompt,
            model_provider=model_provider,
            model_name=model_name,
            max_tokens=4096,
            temperature=0.2
        )
        
        # Try to parse the JSON and validate with Pydantic
        try:
            raw_data = json.loads(response)
            # Add depth=1 to all top-level actors
            for actor in raw_data.get("actors", []):
                actor["depth"] = 1
            actors_list = ActorList(**raw_data)

            # Pretty print the validated data
            print("=" * 80)
            for i, actor in enumerate(actors_list.actors, 1):
                print(f"✅ {i:2d}. {actor.name} ({actor.type})")
                print(f"    📝 Description: {actor.description}")
                print()

            # Get current cost session data
            cost_data = get_cost_session()

            # Prepare the data to save with metadata
            output_data = {
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "run_folder": run_folder.name,
                    "model_provider": model_provider,
                    "model_name": model_name,
                    "num_actors_requested": num_actors,
                    "num_actors_generated": actors_list.total_count,
                    "script_version": "2.0.0",
                    "generation_method": "LLM-based",
                    "level": 0,
                    "cost_tracking": cost_data
                },
                "actors": [actor.model_dump() for actor in actors_list.actors],
                "total_count": actors_list.total_count
            }

            # Save the results to JSON file
            save_level_data(output_data, 0, run_folder)

            log_success(
                f"Level 0 complete! Generated {actors_list.total_count} actors",
                f"Provider: {model_provider}\nModel: {model_name}\nActors: {actors_list.total_count}"
            )

            return actors_list
            
        except json.JSONDecodeError as e:
            # Handle JSON truncation with retry logic
            if "Unterminated string" in str(e) or "Expecting ',' delimiter" in str(e):
                log_error(
                    error_type="JSON_TRUNCATION_ERROR",
                    error_message="LLM response appears to be truncated due to token limit",
                    details=f"Requested {num_actors} actors. Response length: {len(response)} chars",
                    exception=e
                )
                
                # Auto-retry with fewer actors
                if _retry_count == 0 and num_actors > 25:
                    retry_actors = max(25, num_actors // 2)
                    print(f"🔄 Auto-retrying with {retry_actors} actors...")
                    return generate_level_0_actors(model_provider, model_name, retry_actors, 
                                                 run_folder, _retry_count=1)
            
            log_error(
                error_type="JSON_PARSE_ERROR",
                error_message="LLM did not return valid JSON",
                details=f"Provider: {model_provider}, Model: {model_name}",
                exception=e
            )
            return None
            
        except Exception as e:
            log_error(
                error_type="PYDANTIC_VALIDATION_ERROR",
                error_message="Data validation failed - LLM response doesn't match expected schema",
                details=f"Provider: {model_provider}, Model: {model_name}",
                exception=e
            )
            return None
            
    except Exception as e:
        # Determine error type based on exception message
        if "API key" in str(e) or "ANTHROPIC_API_KEY" in str(e) or "OPENAI_API_KEY" in str(e):
            error_type = "API_KEY_ERROR"
            error_message = f"API key not found or invalid for {model_provider}"
        elif "quota" in str(e).lower() or "limit" in str(e).lower():
            error_type = "API_QUOTA_ERROR"
            error_message = f"API quota or rate limit exceeded for {model_provider}"
        else:
            error_type = "GENERAL_API_ERROR"
            error_message = f"Unexpected error when calling {model_provider} API"
        
        log_error(
            error_type=error_type,
            error_message=error_message,
            details=f"Provider: {model_provider}, Model: {model_name}",
            exception=e
        )
        return None

# ==================== ASYNC LEVEL N GENERATION ====================

async def generate_subactors_for_actor_async(actor_data: Dict[str, Any], model_provider: str, 
                                           model_name: str, num_subactors: int, 
                                           current_level: int, actor_index: int = 0) -> SubActorList:
    """Generate sub-actors for a specific actor using LLM (async version)"""
    
    actor_name = actor_data["name"]
    actor_description = actor_data["description"]
    actor_type = actor_data["type"]
    
    # Generate prompts using the centralized prompts module
    system_context, user_context = generate_leveldown_prompts(
        actor_name, actor_description, actor_type, num_subactors, current_level
    )
    
    full_prompt = system_context + user_context
    
    try:
        print(f"🔄 [{actor_index+1}] Generating sub-actors for: {actor_name}")
        
        # Call the async LLM API
        response = await call_llm_api_async(
            prompt=full_prompt,
            model_provider=model_provider,
            model_name=model_name,
            max_tokens=3000,
            temperature=0.3
        )
        
        # Parse and validate the response
        try:
            raw_data = json.loads(response)
            # Inject depth before validation
            for sa in raw_data.get("sub_actors", []):
                sa.setdefault("depth", current_level + 1)
            sub_actors_list = SubActorList(**raw_data)
            
            print(f"✅ [{actor_index+1}] Generated {sub_actors_list.total_count} sub-actors for {actor_name}")
            return sub_actors_list
            
        except json.JSONDecodeError as e:
            log_error(
                error_type="JSON_PARSE_ERROR",
                error_message=f"Failed to parse JSON response for {actor_name}",
                details=f"Response length: {len(response)} characters",
                exception=e
            )
            raise
            
        except Exception as e:
            log_error(
                error_type="VALIDATION_ERROR",
                error_message=f"Data validation failed for {actor_name}",
                details=f"LLM returned valid JSON but doesn't match expected schema",
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

# Synchronous version for backward compatibility
def generate_subactors_for_actor(actor_data: Dict[str, Any], model_provider: str, 
                                model_name: str, num_subactors: int, current_level: int) -> SubActorList:
    """Generate sub-actors for a specific actor using LLM (synchronous version)"""
    
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
            for sa in raw_data.get("sub_actors", []):
                sa.setdefault("depth", current_level + 1)
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
            raise
            
        except Exception as e:
            log_error(
                error_type="VALIDATION_ERROR",
                error_message=f"Data validation failed for {actor_name}",
                details=f"LLM returned valid JSON but doesn't match expected schema",
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

async def generate_level_n_actors_async(source_level: int, target_level: int, model_provider: str, 
                                      model_name: str, num_subactors: int, run_folder: Path, 
                                      skip_on_error: bool = True) -> Optional[List[EnhancedActor]]:
    """Generate Level N actors from Level N-1 (async version with parallelization)"""
    
    print(f"\n🔽 LEVEL {target_level}: Generating sub-actors from Level {source_level}")
    print(f"🔧 Provider: {model_provider}")
    print(f"🤖 Model: {model_name}")
    print(f"📊 Sub-actors per actor: {num_subactors}")
    print(f"🔀 Parallel threads: 5")
    print("=" * 60)
    
    # Load source level data
    source_file = run_folder / f"Features_level_{source_level}.json"
    if not source_file.exists():
        log_error(
            error_type="FILE_NOT_FOUND",
            error_message=f"Source level {source_level} file not found",
            details=f"Expected file: {source_file}"
        )
        return None
    
    with open(source_file, 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    
    parent_actors = source_data.get("actors", [])
    total_subactors = 0
    enhanced_actors = []
    successful_actors = failed_actors = 0
    
    # Get original metadata from level 0 or inherit from source
    if source_level == 0:
        original_metadata = source_data.get("metadata", {})
    else:
        original_metadata = source_data.get("metadata", {}).get("original_metadata", 
                                                               source_data.get("metadata", {}))
    
    if source_level == 0:
        # Level 1: Process main actors in parallel
        tasks = []
        actors_to_process = []

        for i, actor_data in enumerate(parent_actors):
            if actor_data.get("sub_actors"):
                # Already has sub-actors – keep them
                enhanced_actors.append(EnhancedActor(**actor_data, depth=1))
                continue

            # Create async task for this actor
            task = generate_subactors_for_actor_async(
                actor_data, model_provider, model_name, num_subactors, target_level, i
            )
            tasks.append(task)
            actors_to_process.append(actor_data)

        # Execute all tasks concurrently
        if tasks:
            print(f"🚀 Starting parallel generation for {len(tasks)} actors...")
            try:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                for i, (actor_data, result) in enumerate(zip(actors_to_process, results)):
                    if isinstance(result, Exception):
                        failed_actors += 1
                        if skip_on_error:
                            print(f"❌ [{i+1}] Skipping {actor_data['name']} due to error")
                            enhanced_actors.append(EnhancedActor(**actor_data, depth=1))
                        else:
                            raise result
                    else:
                        # Set depth=2 for all sub-actors
                        for sub in result.sub_actors:
                            sub.depth = 2
                        enhanced_actors.append(EnhancedActor(
                            name=actor_data["name"],
                            description=actor_data["description"],
                            type=actor_data["type"],
                            sub_actors=result.sub_actors,
                            sub_actors_count=result.total_count,
                            depth=1
                        ))
                        total_subactors += result.total_count
                        successful_actors += 1

            except Exception as e:
                if not skip_on_error:
                    raise

    else:
        # Level N->N+1: Recursively process all leaf nodes at depth==target_level
        leaf_nodes: List[Dict[str, Any]] = []

        def collect_leaves(nodes: List[Dict[str, Any]]):
            for n in nodes:
                # If this node is at the depth we're expanding and has no sub-actors yet → generate
                if n.get("depth") == target_level and (not n.get("sub_actors")):
                    leaf_nodes.append(n)
                # Recurse deeper if there are existing sub-actors
                if n.get("sub_actors"):
                    collect_leaves(n["sub_actors"])

        # Collect all leaves eligible for generation
        collect_leaves(parent_actors)

        # Create tasks for each leaf node
        tasks = []
        for idx, leaf in enumerate(leaf_nodes):
            task = generate_subactors_for_actor_async(
                leaf, model_provider, model_name, num_subactors, target_level, idx
            )
            tasks.append(task)

        # Execute tasks
        if tasks:
            print(f"🚀 Starting parallel generation for {len(tasks)} leaf nodes at depth {target_level}...")
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for leaf, res in zip(leaf_nodes, results):
                if isinstance(res, Exception):
                    failed_actors += 1
                    if not skip_on_error:
                        raise res
                    continue

                # Assign depth to newly generated sub-actors
                for sub in res.sub_actors:
                    sub.depth = target_level + 1

                leaf["sub_actors"] = [sub.model_dump() for sub in res.sub_actors]
                leaf["sub_actors_count"] = res.total_count
                total_subactors += res.total_count
                successful_actors += 1

        # After updates, convert the top-level actors back to EnhancedActor models
        enhanced_actors = [EnhancedActor(**actor) for actor in parent_actors]
        total_main_actors = len(enhanced_actors)
        actors_with_subactors = sum(1 for a in enhanced_actors if a.sub_actors_count > 0)
        avg_subactors_per_actor = total_subactors / total_main_actors if total_main_actors else 0
        # Note: above stats recalculated, override previous quick counts
 
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
            "run_folder": run_folder.name,
            "model_provider": model_provider,
            "model_name": model_name,
            "script_version": "2.0.0",
            "level": target_level,
            "parent_file": f"Features_level_{source_level}.json",
            "original_metadata": original_metadata,
            "parallelization": {
                "enabled": True,
                "max_concurrent_threads": 5,
                "total_parallel_tasks": len(tasks) if 'tasks' in locals() else 0
            },
            "generation_stats": {
                "total_main_actors": total_main_actors,
                "total_subactors": total_subactors,
                "actors_with_subactors": actors_with_subactors,
                "avg_subactors_per_actor": round(avg_subactors_per_actor, 2),
                "successful_actors": successful_actors,
                "failed_actors": failed_actors
            },
            "cost_tracking": cost_data
        },
        "actors": [actor.model_dump() for actor in enhanced_actors],
        "total_main_actors": total_main_actors,
        "total_subactors": total_subactors,
        "level": target_level
    }
    
    # Save the level data
    save_level_data(output_data, target_level, run_folder)
    
    log_success(
        f"Level {target_level} complete! Generated {total_subactors} sub-actors",
        f"Successful: {successful_actors}, Failed: {failed_actors}\n"
        f"Total main actors: {total_main_actors}\n"
        f"Average sub-actors per actor: {avg_subactors_per_actor:.2f}\n"
        f"Parallel tasks executed: {len(tasks) if 'tasks' in locals() else 0}"
    )
    
    return enhanced_actors

# Synchronous version for backward compatibility
def generate_level_n_actors(source_level: int, target_level: int, model_provider: str, 
                           model_name: str, num_subactors: int, run_folder: Path, 
                           skip_on_error: bool = True) -> Optional[List[EnhancedActor]]:
    """Generate Level N actors from Level N-1 (synchronous version)"""
    
    print(f"\n🔽 LEVEL {target_level}: Generating sub-actors from Level {source_level}")
    print(f"🔧 Provider: {model_provider}")
    print(f"🤖 Model: {model_name}")
    print(f"📊 Sub-actors per actor: {num_subactors}")
    print("=" * 60)
    
    # Load source level data
    source_file = run_folder / f"Features_level_{source_level}.json"
    if not source_file.exists():
        log_error(
            error_type="FILE_NOT_FOUND",
            error_message=f"Source level {source_level} file not found",
            details=f"Expected file: {source_file}"
        )
        return None
    
    with open(source_file, 'r', encoding='utf-8') as f:
        source_data = json.load(f)
    
    parent_actors = source_data.get("actors", [])
    total_subactors = 0
    enhanced_actors = []
    successful_actors = failed_actors = 0
    
    # Get original metadata from level 0 or inherit from source
    if source_level == 0:
        original_metadata = source_data.get("metadata", {})
    else:
        original_metadata = source_data.get("metadata", {}).get("original_metadata", 
                                                               source_data.get("metadata", {}))
    
    if source_level == 0:
        # Level 0->1: Process main actors
        for actor_data in parent_actors:
            actor_name = actor_data["name"]
            if actor_data.get("sub_actors"):
                # Already has sub-actors – keep them
                enhanced_actors.append(EnhancedActor(**actor_data, depth=1))
                continue

            try:
                sub_list = generate_subactors_for_actor(actor_data, model_provider, 
                                                       model_name, num_subactors, target_level)
                enhanced_actors.append(EnhancedActor(
                    name=actor_data["name"],
                    description=actor_data["description"],
                    type=actor_data["type"],
                    sub_actors=sub_list.sub_actors,
                    sub_actors_count=sub_list.total_count,
                    depth=1
                ))
                total_subactors += sub_list.total_count
                successful_actors += 1
            except Exception as e:
                failed_actors += 1
                if skip_on_error:
                    enhanced_actors.append(EnhancedActor(**actor_data, depth=1))
                else:
                    raise
    else:
        # Level N->N+1: Process sub-actors from previous level
        for main_actor in parent_actors:
            updated_sub_actors = []
            for sub_actor in main_actor.get("sub_actors", []):
                if sub_actor.get("sub_actors"):
                    # Sub-actor already has sub-actors – keep them
                    updated_sub_actors.append(SubActor(**sub_actor, depth=target_level))
                    continue
                
                try:
                    sub_list = generate_subactors_for_actor(sub_actor, model_provider, 
                                                           model_name, num_subactors, target_level)
                    updated_sub_actor = SubActor(
                        name=sub_actor["name"],
                        description=sub_actor["description"],
                        type=sub_actor["type"],
                        parent_actor=sub_actor["parent_actor"],
                        sub_actors=sub_list.sub_actors,
                        sub_actors_count=sub_list.total_count,
                        depth=target_level
                    )
                    updated_sub_actors.append(updated_sub_actor)
                    total_subactors += sub_list.total_count
                    successful_actors += 1
                except Exception as e:
                    failed_actors += 1
                    if skip_on_error:
                        updated_sub_actors.append(SubActor(**sub_actor, depth=target_level))
                    else:
                        raise
            
            # Create enhanced main actor with updated sub-actors
            enhanced_actors.append(EnhancedActor(
                name=main_actor["name"],
                description=main_actor["description"],
                type=main_actor["type"],
                sub_actors=updated_sub_actors,
                sub_actors_count=len(updated_sub_actors),
                depth=main_actor.get("depth", max(1, target_level-1))
            ))
    
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
            "run_folder": run_folder.name,
            "model_provider": model_provider,
            "model_name": model_name,
            "script_version": "2.0.0",
            "level": target_level,
            "parent_file": f"Features_level_{source_level}.json",
            "original_metadata": original_metadata,
            "parallelization": {
                "enabled": False,
                "max_concurrent_threads": 1,
                "total_parallel_tasks": 0
            },
            "generation_stats": {
                "total_main_actors": total_main_actors,
                "total_subactors": total_subactors,
                "actors_with_subactors": actors_with_subactors,
                "avg_subactors_per_actor": round(avg_subactors_per_actor, 2),
                "successful_actors": successful_actors,
                "failed_actors": failed_actors
            },
            "cost_tracking": cost_data
        },
        "actors": [actor.model_dump() for actor in enhanced_actors],
        "total_main_actors": total_main_actors,
        "total_subactors": total_subactors,
        "level": target_level
    }
    
    # Save the level data
    save_level_data(output_data, target_level, run_folder)
    
    log_success(
        f"Level {target_level} complete! Generated {total_subactors} sub-actors",
        f"Successful: {successful_actors}, Failed: {failed_actors}\n"
        f"Total main actors: {total_main_actors}\n"
        f"Average sub-actors per actor: {avg_subactors_per_actor:.2f}"
    )
    
    return enhanced_actors

# ==================== MAIN GENERATION FUNCTION ====================

async def generate_complete_world_model_async(model_provider: str = "anthropic", 
                                            model_name: str = "claude-3-5-sonnet-latest",
                                            target_depth: int = 3,
                                            level_counts: Optional[List[int]] = None,
                                            skip_on_error: bool = True) -> Optional[Path]:
    """
    Generate a complete world model with all levels from 0 to target_depth (async version)
    
    Args:
        model_provider: LLM provider to use
        model_name: Specific model name
        target_depth: Maximum depth to generate (0 = only initial actors)
        level_counts: List of four integers specifying the number of actors/sub-actors
                      for each level (L0, L1, L2, L3).
        skip_on_error: Whether to skip actors that fail generation
        
    Returns:
        Path to the run folder containing all generated files
    """
    
    print(f"🌍 STARTING COMPLETE WORLD MODEL GENERATION (ASYNC)")
    print(f"🔧 Provider: {model_provider}")
    print(f"🤖 Model: {model_name}")
    if level_counts is None:
        level_counts = [10, 8, 0, 0]  # sensible defaults if none supplied

    # Ensure exactly 4 elements
    if len(level_counts) < 4:
        level_counts = level_counts + [0] * (4 - len(level_counts))
    elif len(level_counts) > 4:
        level_counts = level_counts[:4]

    num_actors = level_counts[0]

    print(f"📊 Level counts (L0-L3): {level_counts}")
    print(f"🔢 Target depth: {target_depth}")
    print(f"🔀 Parallel threads: 5")
    print(f"⚠️  Skip on error: {skip_on_error}")
    print("=" * 80)
    
    # Reset cost session for the entire run
    reset_cost_session()
    
    # Create run folder
    run_folder = get_run_folder_path()
    
    try:
        # Generate Level 0 (Initial actors) - still synchronous as it's usually just one request
        log_info("Starting Level 0 generation", 
                f"Generating {num_actors} initial world actors")
        
        level_0_actors = generate_level_0_actors(model_provider, model_name, num_actors, run_folder)
        
        if not level_0_actors:
            log_error(
                error_type="LEVEL_0_FAILED",
                error_message="Failed to generate Level 0 actors",
                details="Cannot proceed with level-down generation"
            )
            return None
        
        # Generate additional levels if requested (using async parallelization)
        if target_depth > 0:
            for level in range(1, target_depth + 1):
                # Determine how many sub-actors to generate at this depth
                level_subactors = level_counts[level] if level < len(level_counts) else 0

                if level_subactors <= 0:
                    log_info(
                        f"Skipping Level {level} generation – sub-actor count is 0",
                        f"Provided level_counts: {level_counts}"
                    )
                    break

                log_info(
                    f"Starting Level {level} generation (parallel)",
                    f"Generating {level_subactors} sub-actors from Level {level-1}"
                )

                enhanced_actors = await generate_level_n_actors_async(
                    source_level=level-1,
                    target_level=level,
                    model_provider=model_provider,
                    model_name=model_name,
                    num_subactors=level_subactors,
                    run_folder=run_folder,
                    skip_on_error=skip_on_error
                )
                
                if not enhanced_actors:
                    log_error(
                        error_type=f"LEVEL_{level}_FAILED",
                        error_message=f"Failed to generate Level {level} actors",
                        details=f"Stopping at Level {level-1}"
                    )
                    break
        
        # Final cost summary
        print("\n" + "=" * 80)
        print("🎉 WORLD MODEL GENERATION COMPLETE! (ASYNC)")
        print("=" * 80)
        print(f"📁 Run folder: {run_folder.name}")
        print(f"🔢 Levels generated: 0 to {target_depth}")
        print(f"🔀 Parallelization: 5 concurrent threads")
        print(f"💰 Final cost summary:")
        print_cost_summary()
        
        return run_folder
        
    except Exception as e:
        log_error(
            error_type="GENERATION_FAILED",
            error_message="Complete world model generation failed",
            details=f"Run folder: {run_folder.name}",
            exception=e
        )
        return None

# Synchronous wrapper for backward compatibility
def generate_complete_world_model(model_provider: str = "anthropic", 
                                 model_name: str = "claude-3-5-sonnet-latest",
                                 target_depth: int = 3,
                                 level_counts: Optional[List[int]] = None,
                                 skip_on_error: bool = True) -> Optional[Path]:
    """
    Synchronous wrapper for the async world model generation
    """
    return asyncio.run(generate_complete_world_model_async(
        model_provider=model_provider,
        model_name=model_name,
        target_depth=target_depth,
        level_counts=level_counts,
        skip_on_error=skip_on_error
    ))

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    # Default values
    provider = "anthropic"
    model = "claude-3-5-sonnet-latest"
    target_depth = 3
    level_counts: List[int] = [10, 8, 0, 0]
    skip_errors = True

    # Parse command line arguments (see docstring for expected order)
    args = sys.argv

    if len(args) > 1:
        provider = args[1]
    if len(args) > 2:
        model = args[2]
    if len(args) > 3:
        try:
            target_depth = int(args[3])
            if target_depth < 0 or target_depth > 3:
                print("⚠️ Warning: target_depth must be between 0-3. Using 3.")
                target_depth = min(max(target_depth, 0), 3)
        except ValueError:
            print(f"⚠️ Warning: Invalid target_depth: '{args[3]}', using 3")

    # Level counts parsing
    if len(args) > 4:
        counts_arg = args[4]
        try:
            if "," in counts_arg:
                level_counts = [int(x.strip()) for x in counts_arg.split(",")]
            else:
                # Accept space-separated counts after target_depth
                level_counts = []
                idx = 4
                while idx < len(args) and len(level_counts) < 4:
                    level_counts.append(int(args[idx]))
                    idx += 1
            # Normalise to exactly 4 ints
            if len(level_counts) < 4:
                level_counts += [0] * (4 - len(level_counts))
            elif len(level_counts) > 4:
                level_counts = level_counts[:4]
        except ValueError:
            print(f"⚠️ Warning: Invalid level_counts argument: '{counts_arg}', using default [10,8,0,0]")
            level_counts = [10, 8, 0, 0]

    # skip_errors flag (last arg)
    if len(args) > 5 and args[-1].lower() in ['true', 'false', '1', '0', 'yes', 'no', 'on', 'off']:
        skip_errors = args[-1].lower() in ['true', '1', 'yes', 'on']
 
    try:
        result = asyncio.run(generate_complete_world_model_async(
            model_provider=provider,
            model_name=model,
            target_depth=target_depth,
            level_counts=level_counts,
            skip_on_error=skip_errors
        ))
        
        if result:
            print(f"\n🎉 SUCCESS! World model generation completed! (with parallelization)")
            print(f"📁 Results saved in: {result}")
            print(f"🔢 Generated levels: 0 to {target_depth}")
            print(f"📊 Level counts (L0-L3): {level_counts}")
            print(f"📊 Total actors: {level_counts[0]}")
            print(f"📊 Sub-actors per level: {level_counts[1:]}")
            print(f"🔀 Parallel threads: 5")
        else:
            print(f"\n❌ FAILED! World model generation failed.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️ Generation interrupted by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        log_error(
            error_type="UNEXPECTED_ERROR",
            error_message="Unexpected error during world model generation",
            details=f"Provider: {provider}, Model: {model}, Level counts: {level_counts}, "
                   f"Depth: {target_depth}",
            exception=e
        )
        sys.exit(1) 



        # How to run this script with all parameters from the terminal:
        #
        # Usage:
        #   python actors_complete.py <provider> <model> <target_depth> "<l0,l1,l2,l3>" <skip_errors>
        #
        # Arguments:
        #   <provider>      : The model provider to use (e.g., "openai", "anthropic")
        #   <model>         : The model name (e.g., "gpt-4", "claude-3-5-sonnet-latest")
        #   <level_counts>  : Comma-separated list of FOUR ints – number of actors at each level
        #   <target_depth>  : How many levels deep to generate (0-3)
        #   <skip_errors>   : Whether to skip errors and continue (true/false/1/0/yes/no)
        #
        # Example:
        #   python actors_complete.py anthropic claude-3-5-sonnet-latest 3 "5,3,5,0" true
        #
        # This will generate a world model using the Anthropic Claude 3.5 Sonnet model,
        # with 5 top-level actors, 3 sub-actors at depth-1, 5 at depth-2, and no generation at depth-3.
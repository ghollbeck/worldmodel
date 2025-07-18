"""
Service layer for the World Model backend.
Handles all business logic for actor and parameter generation.
"""

import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from .config import get_config
from .models import (
    Actor, ActorList, SubActor, SubActorList, EnhancedActor, ActorParameter,
    GenerationMetadata, ParallelizationMetadata, GenerationStats, CostTracking,
    CompleteMetadata, GenerationOutput, GenerationStatus, SystemStatus
)
from .utils import (
    log_error, log_success, log_info, log_warning,
    get_run_folder_path, get_latest_run_folder, save_level_data, load_level_data,
    call_llm_api_async, handle_json_parsing_error, handle_api_error, validate_actor_data
)
from .llm.llm import call_llm_api, get_cost_session, reset_cost_session
from .routes.initializationroute.prompts import generate_initial_actor_prompts, generate_leveldown_prompts
# Import functions from the prepared parameter generation script
from .routes.initializationroute.generate_parameters_for_actors import (
    generate_parameters_for_actor, 
    add_parameters_recursively,
    count_actors_recursively,
    find_latest_deepest_json
)


class GenerationService:
    """Service class for handling actor and parameter generation"""
    
    def __init__(self):
        self.config = get_config()
        self.actor_status = GenerationStatus(
            status="idle",
            message="Ready to generate actors"
        )
        self.parameter_status = GenerationStatus(
            status="idle",
            message="Ready to generate parameters"
        )
    
    def get_status(self) -> SystemStatus:
        """Get current system status"""
        return SystemStatus(
            actors=self.actor_status,
            parameters=self.parameter_status
        )
    
    def update_actor_status(self, status: str, message: str, 
                           progress: Optional[float] = None, 
                           details: Optional[Dict[str, Any]] = None,
                           error: Optional[str] = None):
        """Update actor generation status"""
        self.actor_status.status = status
        self.actor_status.message = message
        self.actor_status.progress = progress
        self.actor_status.details = details
        self.actor_status.error = error
        
        if status == "running" and self.actor_status.start_time is None:
            self.actor_status.start_time = datetime.now().isoformat()
        elif status in ["completed", "failed"]:
            self.actor_status.end_time = datetime.now().isoformat()
    
    def update_parameter_status(self, status: str, message: str, 
                              progress: Optional[float] = None, 
                              details: Optional[Dict[str, Any]] = None,
                              error: Optional[str] = None):
        """Update parameter generation status"""
        self.parameter_status.status = status
        self.parameter_status.message = message
        self.parameter_status.progress = progress
        self.parameter_status.details = details
        self.parameter_status.error = error
        
        if status == "running" and self.parameter_status.start_time is None:
            self.parameter_status.start_time = datetime.now().isoformat()
        elif status in ["completed", "failed"]:
            self.parameter_status.end_time = datetime.now().isoformat()

    async def generate_actors_async(self, provider: str, model: str, 
                                  num_actors: int, num_subactors: int, 
                                  target_depth: int, skip_on_error: bool = True) -> Optional[Path]:
        """
        Generate complete world model with actors (async version)
        """
        
        # Update status
        self.update_actor_status("running", "Starting actor generation", 0)
        
        # --- Delegated generation using actors_complete script ---
        from worldmodel.backend.routes.initializationroute import actors_complete as ac
        try:
            run_folder = await ac.generate_complete_world_model_async(
                model_provider=provider,
                model_name=model,
                num_actors=num_actors,
                num_subactors=num_subactors,
                target_depth=target_depth,
                skip_on_error=skip_on_error
            )
            print(f"🔧 Run OG script complete")
            if run_folder:
                self.update_actor_status(
                    "completed",
                    f"Successfully generated {target_depth + 1} levels (delegated)",
                    100,
                    {"run_folder": run_folder.name, "levels": target_depth + 1}
                )
                log_success(
                    "World model generation complete (delegated to actors_complete)",
                    f"Run folder: {run_folder.name}, Levels: 0-{target_depth}"
                )
            else:
                self.update_actor_status(
                    "failed",
                    "actors_complete script failed",
                    error="Delegated script returned no result"
                )
            return run_folder
        except Exception as e:
            self.update_actor_status("failed", "Generation failed", error=str(e))
            log_error(
                error_type="GENERATION_FAILED",
                error_message="Delegated world model generation failed",
                exception=e
            )
            return None
        # -------------------------------------------------------------------
        
        # The original in-house generation logic is retained below for reference
        # but will not be executed because of the early return above.
        
        # try:
        #     # Reset cost session
        #     reset_cost_session()
            
        #     # Create run folder
        #     run_folder = get_run_folder_path()
            
        #     log_info(
        #         f"Starting complete world model generation",
        #         f"Provider: {provider}, Model: {model}, Actors: {num_actors}, "
        #         f"Sub-actors: {num_subactors}, Depth: {target_depth}"
        #     )
            
        #     # Generate Level 0 (Initial actors)
        #     self.update_actor_status("running", "Generating initial actors", 10)
            
        #     level_0_actors = await self._generate_level_0_actors(
        #         provider, model, num_actors, run_folder
        #     )
            
        #     if not level_0_actors:
        #         self.update_actor_status("failed", "Failed to generate initial actors", 
        #                                error="Level 0 generation failed")
        #         return None
            
        #     # Generate additional levels if requested
        #     if target_depth > 0:
        #         for level in range(1, target_depth + 1):
        #             progress = 10 + (level * 80) / target_depth
        #             self.update_actor_status("running", 
        #                                    f"Generating level {level} sub-actors", 
        #                                    progress)
                    
        #             enhanced_actors = await self._generate_level_n_actors_async(
        #                 source_level=level-1,
        #                 target_level=level,
        #                 provider=provider,
        #                 model=model,
        #                 num_subactors=num_subactors,
        #                 run_folder=run_folder,
        #                 skip_on_error=skip_on_error
        #             )
                    
        #             if not enhanced_actors:
        #                 self.update_actor_status("failed", 
        #                                        f"Failed to generate level {level} actors",
        #                                        error=f"Level {level} generation failed")
        #                 return None
            
        #     # Complete
        #     self.update_actor_status("completed", 
        #                            f"Successfully generated {target_depth + 1} levels", 
        #                            100,
        #                            {"run_folder": run_folder.name, "levels": target_depth + 1})
            
        #     log_success(
        #         f"World model generation complete",
        #         f"Run folder: {run_folder.name}, Levels: 0-{target_depth}"
        #     )
            
        #     return run_folder
            
        # except Exception as e:
        #     self.update_actor_status("failed", "Generation failed", 
        #                            error=str(e))
        #     log_error(
        #         error_type="GENERATION_FAILED",
        #         error_message="Complete world model generation failed",
        #         exception=e
        #     )
        #     return None

    async def _generate_level_0_actors(self, provider: str, model: str, 
                                     num_actors: int, run_folder: Path) -> Optional[ActorList]:
        """Generate Level 0 (initial) actors"""
        
        log_info(f"Generating {num_actors} initial world actors")
        
        # Generate prompts
        system_context, user_context = generate_initial_actor_prompts(num_actors)
        full_prompt = system_context + user_context
        
        try:
            # Call LLM API
            response = await call_llm_api_async(
                call_llm_api,
                prompt=full_prompt,
                model_provider=provider,
                model_name=model,
                max_tokens=self.config.llm.max_tokens,
                temperature=self.config.llm.temperature
            )
            
            # Parse and validate response
            try:
                raw_data = json.loads(response)
                actors_list = ActorList(**raw_data)
                
                # Prepare output data
                cost_data = get_cost_session()
                output_data = {
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "run_folder": run_folder.name,
                        "model_provider": provider,
                        "model_name": model,
                        "num_actors_requested": num_actors,
                        "num_actors_generated": actors_list.total_count,
                        "script_version": self.config.script_version,
                        "generation_method": "LLM-based",
                        "level": 0,
                        "cost_tracking": cost_data
                    },
                    "actors": [actor.model_dump() for actor in actors_list.actors],
                    "total_count": actors_list.total_count
                }
                
                # Save results
                save_level_data(output_data, 0, run_folder)
                
                return actors_list
                
            except json.JSONDecodeError as e:
                handle_json_parsing_error(response, f"Level 0 generation with {num_actors} actors")
                return None
            except Exception as e:
                log_error(
                    error_type="PYDANTIC_VALIDATION_ERROR",
                    error_message="Data validation failed",
                    details=f"Provider: {provider}, Model: {model}",
                    exception=e
                )
                return None
                
        except Exception as e:
            error_type = handle_api_error(e, provider, model)
            log_error(
                error_type=error_type,
                error_message=f"API error during Level 0 generation",
                details=f"Provider: {provider}, Model: {model}",
                exception=e
            )
            return None

    async def _generate_subactors_for_actor_async(self, actor_data: Dict[str, Any], 
                                                provider: str, model: str, 
                                                num_subactors: int, current_level: int,
                                                actor_index: int = 0) -> SubActorList:
        """Generate sub-actors for a specific actor (async version)"""
        
        actor_name = actor_data["name"]
        actor_description = actor_data["description"]
        actor_type = actor_data["type"]
        
        # Generate prompts
        system_context, user_context = generate_leveldown_prompts(
            actor_name, actor_description, actor_type, num_subactors, current_level
        )
        full_prompt = system_context + user_context
        
        try:
            # Call LLM API
            response = await call_llm_api_async(
                call_llm_api,
                prompt=full_prompt,
                model_provider=provider,
                model_name=model,
                max_tokens=3000,
                temperature=0.3
            )
            
            # Parse and validate response
            try:
                raw_data = json.loads(response)
                sub_actors_list = SubActorList(**raw_data)
                
                log_info(f"Generated {sub_actors_list.total_count} sub-actors for {actor_name}")
                return sub_actors_list
                
            except json.JSONDecodeError as e:
                handle_json_parsing_error(response, f"Sub-actor generation for {actor_name}")
                raise
            except Exception as e:
                log_error(
                    error_type="VALIDATION_ERROR",
                    error_message=f"Data validation failed for {actor_name}",
                    exception=e
                )
                raise
                
        except Exception as e:
            log_error(
                error_type="SUBACTOR_GENERATION_ERROR",
                error_message=f"Failed to generate sub-actors for {actor_name}",
                details=f"Provider: {provider}, Model: {model}",
                exception=e
            )
            raise

    async def _generate_level_n_actors_async(self, source_level: int, target_level: int,
                                           provider: str, model: str, num_subactors: int,
                                           run_folder: Path, skip_on_error: bool = True) -> Optional[List[EnhancedActor]]:
        """Generate Level N actors from Level N-1 (async version)"""
        
        log_info(f"Generating Level {target_level} sub-actors from Level {source_level}")
        
        # Load source level data
        source_data = load_level_data(source_level, run_folder)
        if not source_data:
            return None
        
        parent_actors = source_data.get("actors", [])
        total_subactors = 0
        enhanced_actors = []
        successful_actors = failed_actors = 0
        
        # Get original metadata
        if source_level == 0:
            original_metadata = source_data.get("metadata", {})
        else:
            original_metadata = source_data.get("metadata", {}).get("original_metadata", 
                                                                   source_data.get("metadata", {}))
        
        if source_level == 0:
            # Level 0->1: Process main actors in parallel
            tasks = []
            actors_to_process = []
            
            for i, actor_data in enumerate(parent_actors):
                if actor_data.get("sub_actors"):
                    # Already has sub-actors
                    enhanced_actors.append(EnhancedActor(**actor_data))
                    continue
                
                # Create async task
                task = self._generate_subactors_for_actor_async(
                    actor_data, provider, model, num_subactors, target_level, i
                )
                tasks.append(task)
                actors_to_process.append(actor_data)
            
            # Execute tasks concurrently
            if tasks:
                log_info(f"Starting parallel generation for {len(tasks)} actors")
                try:
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    # Process results
                    for i, (actor_data, result) in enumerate(zip(actors_to_process, results)):
                        if isinstance(result, Exception):
                            failed_actors += 1
                            if skip_on_error:
                                log_warning(f"Skipping {actor_data['name']} due to error")
                                enhanced_actors.append(EnhancedActor(**actor_data))
                            else:
                                raise result
                        else:
                            enhanced_actors.append(EnhancedActor(
                                name=actor_data["name"],
                                description=actor_data["description"],
                                type=actor_data["type"],
                                sub_actors=result.sub_actors,
                                sub_actors_count=result.total_count,
                            ))
                            total_subactors += result.total_count
                            successful_actors += 1
                            
                except Exception as e:
                    if not skip_on_error:
                        raise
        else:
            # Level N->N+1: Process sub-actors (implementation similar to above)
            # For brevity, implementing basic version - can be expanded
            for main_actor in parent_actors:
                enhanced_actors.append(EnhancedActor(**main_actor))
        
        # Prepare output data
        cost_data = get_cost_session()
        output_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "run_folder": run_folder.name,
                "model_provider": provider,
                "model_name": model,
                "script_version": self.config.script_version,
                "level": target_level,
                "parent_file": f"Features_level_{source_level}.json",
                "original_metadata": original_metadata,
                "parallelization": {
                    "enabled": True,
                    "max_concurrent_threads": self.config.llm.max_concurrent_requests,
                    "total_parallel_tasks": len(tasks) if 'tasks' in locals() else 0
                },
                "generation_stats": {
                    "total_main_actors": len(enhanced_actors),
                    "total_subactors": total_subactors,
                    "successful_actors": successful_actors,
                    "failed_actors": failed_actors
                },
                "cost_tracking": cost_data
            },
            "actors": [actor.model_dump() for actor in enhanced_actors],
            "total_main_actors": len(enhanced_actors),
            "total_subactors": total_subactors,
            "level": target_level
        }
        
        # Save results
        save_level_data(output_data, target_level, run_folder)
        
        return enhanced_actors

    async def generate_parameters_async(self, provider: str, model: str, 
                                      num_params: int) -> Optional[Path]:
        """Generate parameters for existing actors using the prepared script"""
        
        self.update_parameter_status("running", "Starting parameter generation", 0)
        
        try:
            # Find latest deepest JSON file using the prepared script's function
            init_logs_dir = get_latest_run_folder().parent if get_latest_run_folder() else None
            if not init_logs_dir:
                self.update_parameter_status("failed", "No actor data found", 
                                           error="No previous runs found")
                return None
                
            try:
                features_json_path = find_latest_deepest_json(init_logs_dir)
            except FileNotFoundError as e:
                self.update_parameter_status("failed", "No features file found", 
                                           error=str(e))
                return None
            
            self.update_parameter_status("running", "Loading actor data", 10)
            
            # Load data using the prepared script's approach
            with open(features_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Count total actors first using the prepared script's function
            actors = data.get('actors', [])
            total_actors = sum(count_actors_recursively(actor) for actor in actors)
            
            log_info(
                "Parameter generation started",
                f"Total actors to process: {total_actors}, Parameters per actor: {num_params}"
            )
            
            self.update_parameter_status("running", f"Processing {total_actors} actors", 20)
            
            # Process each main actor using the prepared script's recursive function
            processed_actors = 0
            for actor in actors:
                # Use the prepared script's recursive function
                await self._add_parameters_recursively_async(
                    actor, num_params, provider, model
                )
                
                processed_actors += count_actors_recursively(actor)
                progress = 20 + (processed_actors * 70) / total_actors
                self.update_parameter_status("running", 
                                           f"Processed {processed_actors}/{total_actors} actors", 
                                           progress)
            
            # Save updated data
            self.update_parameter_status("running", "Saving results", 90)
            
            out_path = features_json_path.parent / (features_json_path.stem + "_with_params.json")
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.update_parameter_status("completed", 
                                       f"Successfully generated {num_params} parameters per actor", 
                                       100,
                                       {"output_file": out_path.name, "total_actors": total_actors})
            
            log_success(f"Parameters generated successfully", f"Output: {out_path}")
            
            return out_path
            
        except Exception as e:
            self.update_parameter_status("failed", "Parameter generation failed", 
                                       error=str(e))
            log_error(
                error_type="PARAMETER_GENERATION_FAILED",
                error_message="Parameter generation failed",
                exception=e
            )
            return None

    async def _add_parameters_recursively_async(self, actor: Dict[str, Any], 
                                               num_params: int, provider: str, model: str):
        """Add parameters to this actor and all sub-actors recursively using async calls"""
        
        # Generate parameters for this actor using the prepared script's function
        actor_params = await call_llm_api_async(
            generate_parameters_for_actor,
            actor, num_params, provider, model
        )
        actor['parameters'] = actor_params
        
        # Recursively process sub-actors
        if 'sub_actors' in actor and isinstance(actor['sub_actors'], list):
            for sub_actor in actor['sub_actors']:
                await self._add_parameters_recursively_async(
                    sub_actor, num_params, provider, model
                )


# Global service instance
generation_service = GenerationService()


def get_generation_service() -> GenerationService:
    """Get the global generation service instance"""
    return generation_service


# Export service
__all__ = [
    'GenerationService',
    'generation_service',
    'get_generation_service'
] 
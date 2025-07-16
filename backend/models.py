"""
Data models for the World Model system.
All Pydantic models for actors, sub-actors, and related data structures.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class Actor(BaseModel):
    """Represents a single actor in the world model"""
    name: str = Field(..., description="The name of the actor")
    description: str = Field(..., description="A short description of the actor's role and influence")
    type: str = Field(..., description="The type of actor")


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
    parameters: List[Dict[str, Any]] = Field(default=[], description="Parameters for this sub-actor")


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
    parameters: List[Dict[str, Any]] = Field(default=[], description="Parameters for this actor")


class ActorParameter(BaseModel):
    """Represents a parameter for an actor"""
    code_name: str = Field(..., description="Short, snake_case name suitable for coding")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="1-2 sentence description")
    type: str = Field(..., description="Data type (string, integer, float, boolean, etc.)")
    expected_value: str = Field(..., description="Example value or range")


class GenerationMetadata(BaseModel):
    """Metadata for generation runs"""
    timestamp: str = Field(..., description="ISO timestamp of generation")
    run_folder: str = Field(..., description="Name of the run folder")
    model_provider: str = Field(..., description="LLM provider used")
    model_name: str = Field(..., description="Specific model used")
    script_version: str = Field(..., description="Version of the generation script")
    level: int = Field(..., description="Level of the generation (0, 1, 2, etc.)")
    parent_file: Optional[str] = Field(None, description="Parent file for level > 0")
    generation_method: str = Field("LLM-based", description="Method used for generation")


class ParallelizationMetadata(BaseModel):
    """Metadata about parallelization"""
    enabled: bool = Field(..., description="Whether parallelization was enabled")
    max_concurrent_threads: int = Field(..., description="Maximum concurrent threads used")
    total_parallel_tasks: int = Field(..., description="Total number of parallel tasks executed")


class GenerationStats(BaseModel):
    """Statistics for generation runs"""
    total_main_actors: int = Field(..., description="Total number of main actors")
    total_subactors: int = Field(..., description="Total number of sub-actors generated")
    actors_with_subactors: int = Field(..., description="Number of actors that have sub-actors")
    avg_subactors_per_actor: float = Field(..., description="Average sub-actors per actor")
    successful_actors: int = Field(..., description="Number of successfully processed actors")
    failed_actors: int = Field(..., description="Number of failed actors")


class CostTracking(BaseModel):
    """Cost tracking information"""
    total_cost: float = Field(0.0, description="Total cost in USD")
    total_tokens: int = Field(0, description="Total tokens used")
    requests_made: int = Field(0, description="Number of API requests made")
    provider_breakdown: Dict[str, Dict[str, Any]] = Field(default={}, description="Cost breakdown by provider")


class CompleteMetadata(BaseModel):
    """Complete metadata for generation files"""
    timestamp: str = Field(..., description="ISO timestamp of generation")
    run_folder: str = Field(..., description="Name of the run folder")
    model_provider: str = Field(..., description="LLM provider used")
    model_name: str = Field(..., description="Specific model used")
    script_version: str = Field(..., description="Version of the generation script")
    level: int = Field(..., description="Level of the generation")
    parent_file: Optional[str] = Field(None, description="Parent file for level > 0")
    original_metadata: Optional[Dict[str, Any]] = Field(None, description="Original metadata from level 0")
    parallelization: ParallelizationMetadata = Field(..., description="Parallelization metadata")
    generation_stats: GenerationStats = Field(..., description="Generation statistics")
    cost_tracking: CostTracking = Field(..., description="Cost tracking information")


class GenerationOutput(BaseModel):
    """Complete output structure for generation files"""
    metadata: CompleteMetadata = Field(..., description="Complete metadata")
    actors: List[EnhancedActor] = Field(..., description="List of enhanced actors")
    total_main_actors: int = Field(..., description="Total number of main actors")
    total_subactors: int = Field(..., description="Total number of sub-actors")
    level: int = Field(..., description="Level of this generation")


# API Request/Response Models
class GenerateActorsRequest(BaseModel):
    """Request model for actor generation"""
    provider: str = Field(..., description="LLM provider")
    model: str = Field(..., description="Model name")
    num_actors: int = Field(..., description="Number of actors to generate")
    num_subactors: int = Field(..., description="Number of sub-actors per actor")
    target_depth: int = Field(..., description="Target depth for generation")
    skip_on_error: bool = Field(True, description="Whether to skip on error")


class GenerateParametersRequest(BaseModel):
    """Request model for parameter generation"""
    provider: str = Field(..., description="LLM provider")
    model: str = Field(..., description="Model name")
    num_params: int = Field(..., description="Number of parameters per actor")


class GenerationStatus(BaseModel):
    """Status of generation tasks"""
    status: str = Field(..., description="Current status (idle, running, completed, failed)")
    message: str = Field(..., description="Status message")
    progress: Optional[float] = Field(None, description="Progress percentage (0-100)")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")
    start_time: Optional[str] = Field(None, description="Start time of the task")
    end_time: Optional[str] = Field(None, description="End time of the task")
    error: Optional[str] = Field(None, description="Error message if failed")


class SystemStatus(BaseModel):
    """Overall system status"""
    actors: GenerationStatus = Field(..., description="Actor generation status")
    parameters: GenerationStatus = Field(..., description="Parameter generation status")


class RunFileInfo(BaseModel):
    """Information about a run file"""
    level: int = Field(..., description="Level of the file")
    file: str = Field(..., description="Filename")
    size: int = Field(..., description="File size in bytes")
    modified: float = Field(..., description="Last modified timestamp")


class RunInfo(BaseModel):
    """Information about a run"""
    status: str = Field(..., description="Status of the run")
    run_folder: Optional[str] = Field(None, description="Run folder name")
    level_files: Optional[List[RunFileInfo]] = Field(None, description="Files in the run")
    total_levels: Optional[int] = Field(None, description="Total number of levels")


# Resolve forward references
SubActor.model_rebuild()

# Export all models
__all__ = [
    'Actor',
    'ActorList',
    'SubActor',
    'SubActorList',
    'EnhancedActor',
    'ActorParameter',
    'GenerationMetadata',
    'ParallelizationMetadata',
    'GenerationStats',
    'CostTracking',
    'CompleteMetadata',
    'GenerationOutput',
    'GenerateActorsRequest',
    'GenerateParametersRequest',
    'GenerationStatus',
    'SystemStatus',
    'RunFileInfo',
    'RunInfo'
] 
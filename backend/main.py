#!/usr/bin/env python3
"""
FastAPI server for World Model LLM Generation
Provides REST API endpoints for generating actors and parameters
"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from worldmodel.backend.config import get_config, validate_environment
from worldmodel.backend.models import (
    GenerateActorsRequest, GenerateParametersRequest, 
    SystemStatus, RunInfo, RunFileInfo
)
from worldmodel.backend.services import get_generation_service
from worldmodel.backend.utils import (
    get_latest_run_folder, get_run_info, validate_generation_request,
    log_info, log_error, log_warning
)


# ==================== INITIALIZATION ====================

# Initialize configuration
config = get_config()
generation_service = get_generation_service()

# Validate environment
missing_env = validate_environment()
if missing_env:
    log_warning(
        "Missing environment variables",
        f"Missing: {', '.join(missing_env)}. Some features may not work."
    )

log_info("World Model API Server starting", f"Version: {config.script_version}")


# ==================== BACKGROUND TASKS ====================

async def generate_actors_background(provider: str, model: str, num_actors: int, 
                                   num_subactors: int, target_depth: int, skip_on_error: bool):
    """Background task for actor generation"""
    try:
        log_info(
            "Starting actor generation background task",
            f"Provider: {provider}, Model: {model}, Actors: {num_actors}"
        )
        
        result = await generation_service.generate_actors_async(
            provider=provider,
            model=model,
            num_actors=num_actors,
            num_subactors=num_subactors,
            target_depth=target_depth,
            skip_on_error=skip_on_error
        )
        
        if result:
            log_info(
                "Actor generation completed successfully",
                f"Run folder: {result.name}"
            )
        else:
            log_error(
                error_type="BACKGROUND_TASK_FAILED",
                error_message="Actor generation background task failed"
            )
            
    except Exception as e:
        log_error(
            error_type="BACKGROUND_TASK_ERROR",
            error_message="Error in actor generation background task",
            exception=e
        )


async def generate_parameters_background(provider: str, model: str, num_params: int):
    """Background task for parameter generation"""
    try:
        log_info(
            "Starting parameter generation background task",
            f"Provider: {provider}, Model: {model}, Params: {num_params}"
        )
        
        result = await generation_service.generate_parameters_async(
            provider=provider,
            model=model,
            num_params=num_params
        )
        
        if result:
            log_info(
                "Parameter generation completed successfully",
                f"Output file: {result.name}"
            )
        else:
            log_error(
                error_type="BACKGROUND_TASK_FAILED",
                error_message="Parameter generation background task failed"
            )
            
    except Exception as e:
        log_error(
            error_type="BACKGROUND_TASK_ERROR",
            error_message="Error in parameter generation background task",
            exception=e
        )


# ==================== FASTAPI APP ====================

app = FastAPI(
    title="World Model LLM Generation API",
    description="REST API for generating actors and parameters using LLMs",
    version=config.script_version
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== API ENDPOINTS ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "World Model LLM Generation API",
        "version": config.script_version,
        "endpoints": {
            "health": "/health",
            "status": "/api/status",
            "config": "/api/config",
            "generate_actors": "/api/generate/actors",
            "generate_parameters": "/api/generate/parameters",
            "latest_run": "/api/runs/latest",
            "run_data": "/api/runs/data/{level}",
            "all_runs": "/api/runs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": config.script_version,
        "environment": {
            "missing_env_vars": validate_environment(),
            "max_concurrent_requests": config.llm.max_concurrent_requests
        }
    }


@app.get("/api/config")
async def get_api_config():
    """Get API configuration for frontend"""
    return {
        "providers": ["anthropic", "openai"],
        "models": config.model_options,
        "limits": config.limits.model_dump(),
        "defaults": {
            "provider": config.default_provider,
            "num_actors": config.default_num_actors,
            "num_subactors": config.default_num_subactors,
            "target_depth": config.default_target_depth,
            "num_params": config.default_num_params
        }
    }


@app.get("/api/status", response_model=SystemStatus)
async def get_status():
    """Get current system status"""
    return generation_service.get_status()


@app.post("/api/generate/actors")
async def generate_actors(request: GenerateActorsRequest, background_tasks: BackgroundTasks):
    """Generate actors and sub-actors"""
    # Validate request
    validation_errors = validate_generation_request(request.model_dump())
    if validation_errors:
        raise HTTPException(
            status_code=400, 
            detail=f"Validation errors: {', '.join(validation_errors)}"
        )
    
    # Check if already running
    current_status = generation_service.get_status()
    if current_status.actors.status == "running":
        raise HTTPException(
            status_code=409, 
            detail="Actor generation already in progress"
        )
    
    # Validate and clamp parameters
    validated_params = config.validate_generation_params(**request.model_dump())
    
    log_info(
        "Actor generation request received",
        f"Original: {request.model_dump()}\nValidated: {validated_params}"
    )
    
    # Start background task
    background_tasks.add_task(
        generate_actors_background,
        validated_params['provider'],
        validated_params['model'],
        validated_params['num_actors'],
        validated_params['num_subactors'],
        validated_params['target_depth'],
        validated_params['skip_on_error']
    )
    
    return {
        "message": "Actor generation started",
        "status": "running",
        "parameters": validated_params
    }


@app.post("/api/generate/parameters")
async def generate_parameters(request: GenerateParametersRequest, background_tasks: BackgroundTasks):
    """Generate parameters for existing actors"""
    # Validate request
    validation_errors = validate_generation_request(request.model_dump())
    if validation_errors:
        raise HTTPException(
            status_code=400, 
            detail=f"Validation errors: {', '.join(validation_errors)}"
        )
    
    # Check if already running
    current_status = generation_service.get_status()
    if current_status.parameters.status == "running":
        raise HTTPException(
            status_code=409, 
            detail="Parameter generation already in progress"
        )
    
    # Check if we have actor data
    run_folder = get_latest_run_folder()
    if not run_folder:
        raise HTTPException(
            status_code=400, 
            detail="No actor data found. Please generate actors first."
        )
    
    # Validate and clamp parameters
    validated_params = config.validate_generation_params(**request.model_dump())
    
    log_info(
        "Parameter generation request received",
        f"Original: {request.model_dump()}\nValidated: {validated_params}"
    )
    
    # Start background task
    background_tasks.add_task(
        generate_parameters_background,
        validated_params['provider'],
        validated_params['model'],
        validated_params['num_params']
    )
    
    return {
        "message": "Parameter generation started",
        "status": "running",
        "parameters": validated_params
    }


@app.get("/api/runs/latest", response_model=RunInfo)
async def get_latest_run():
    """Get information about the latest run"""
    run_folder = get_latest_run_folder()
    
    if not run_folder:
        return RunInfo(status="no_runs")
    
    return get_run_info(run_folder)


@app.get("/api/runs/data/{level}")
async def get_run_data(level: int):
    """Get data from a specific level of the latest run"""
    run_folder = get_latest_run_folder()
    
    if not run_folder:
        raise HTTPException(status_code=404, detail="No runs found")
    
    # FORCE load the _with_params version for debugging
    file_path = run_folder / f"Features_level_{level}_with_params.json"
    
    # Add logging to show which file is being served
    print(f"🔍 Backend serving file: {file_path}")
    print(f"📁 File exists: {file_path.exists()}")
    
    if not file_path.exists():
        print(f"⚠️  _with_params file not found, falling back to regular file")
        file_path = run_folder / f"Features_level_{level}.json"
        print(f"🔍 Backend serving fallback file: {file_path}")
        print(f"📁 Fallback file exists: {file_path.exists()}")
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Level {level} data not found")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Successfully loaded {file_path.name}")
        print(f"📊 Data contains {len(data.get('actors', []))} actors")
        if data.get('actors'):
            actor_keys = list(data['actors'][0].keys())
            print(f"🔑 First actor keys: {actor_keys}")
            print(f"📋 Has parameters: {'parameters' in actor_keys}")
        return data
    except Exception as e:
        print(f"❌ Error loading {file_path.name}: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading data: {str(e)}")


@app.get("/api/runs/data/{level_str}")
async def get_run_data_with_suffix(level_str: str):
    """Get data from a specific level with optional suffix (e.g., '3_with_params')"""
    run_folder = get_latest_run_folder()
    
    if not run_folder:
        raise HTTPException(status_code=404, detail="No runs found")
    
    file_path = run_folder / f"Features_level_{level_str}.json"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Level {level_str} data not found")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        log_error(
            error_type="DATA_LOAD_ERROR",
            error_message=f"Failed to load level {level_str} data",
            details=f"File: {file_path}",
            exception=e
        )
        raise HTTPException(status_code=500, detail=f"Failed to load data: {str(e)}")


@app.get("/api/runs")
async def get_all_runs():
    """Get information about all runs"""
    backend_dir = Path(__file__).parent
    base_logs_dir = backend_dir / config.base_logs_dir
    
    if not base_logs_dir.exists():
        return {"runs": [], "total": 0}
    
    runs = []
    run_folders = [d for d in base_logs_dir.iterdir() 
                   if d.is_dir() and d.name.startswith("run_")]
    
    run_folders.sort(key=lambda x: x.stat().st_ctime, reverse=True)
    
    for run_folder in run_folders:
        run_info = get_run_info(run_folder)
        runs.append(run_info)
    
    return {"runs": runs, "total": len(runs)}


@app.get("/api/test/params")
async def test_params():
    """Test endpoint to check if _with_params file is loaded correctly"""
    run_folder = get_latest_run_folder()
    
    if not run_folder:
        return {"error": "No runs found"}
    
    # Test both files
    regular_file = run_folder / "Features_level_3.json"
    params_file = run_folder / "Features_level_3_with_params.json"
    
    result = {
        "regular_file_exists": regular_file.exists(),
        "params_file_exists": params_file.exists(),
        "regular_file_size": regular_file.stat().st_size if regular_file.exists() else 0,
        "params_file_size": params_file.stat().st_size if params_file.exists() else 0,
    }
    
    # Try to load params file
    if params_file.exists():
        try:
            with open(params_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            result["params_file_has_parameters"] = "parameters" in str(data)
            result["params_file_actor_keys"] = list(data.get("actors", [{}])[0].keys()) if data.get("actors") else []
        except Exception as e:
            result["params_file_error"] = str(e)
    
    return result


if __name__ == "__main__":
    import uvicorn
    
    log_info(
        f"Starting World Model API server",
        f"Host: {config.api_host}, Port: {config.api_port}"
    )
    
    uvicorn.run(
           app, 
           host=config.api_host, 
           port=config.api_port,
           log_level="info"
       )
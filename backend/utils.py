"""
Utility functions for the World Model backend.
Common functions for logging, file management, and error handling.
"""

import json
import traceback
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from .config import get_config
from .models import GenerationOutput


# ==================== LOGGING FUNCTIONS ====================

def log_error(error_type: str, error_message: str, details: Optional[str] = None, 
              exception: Optional[Exception] = None) -> None:
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


def log_success(message: str, details: Optional[str] = None) -> None:
    """Success logging function with green checkmark emoji"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n{'='*60}")
    print(f"✅ SUCCESS - {timestamp}")
    print(f"{'='*60}")
    print(f"Message: {message}")
    
    if details:
        print(f"Details: {details}")
    
    print(f"{'='*60}\n")


def log_info(message: str, details: Optional[str] = None) -> None:
    """Info logging function with blue info emoji"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n{'='*60}")
    print(f"ℹ️  INFO - {timestamp}")
    print(f"{'='*60}")
    print(f"Message: {message}")
    
    if details:
        print(f"Details: {details}")
    
    print(f"{'='*60}\n")


def log_warning(message: str, details: Optional[str] = None) -> None:
    """Warning logging function with yellow warning emoji"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n{'='*60}")
    print(f"⚠️  WARNING - {timestamp}")
    print(f"{'='*60}")
    print(f"Message: {message}")
    
    if details:
        print(f"Details: {details}")
    
    print(f"{'='*60}\n")


# ==================== FILE MANAGEMENT ====================

def get_run_folder_path() -> Path:
    """Get the path to the most recent run folder or create a new one"""
    config = get_config()
    
    # Get the backend directory - walk up from this file
    backend_dir = Path(__file__).parent
    base_logs_dir = backend_dir / config.base_logs_dir
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


def get_latest_run_folder() -> Optional[Path]:
    """Get the path to the most recent run folder"""
    config = get_config()
    backend_dir = Path(__file__).parent
    base_logs_dir = backend_dir / config.base_logs_dir
    
    if not base_logs_dir.exists():
        return None
    
    # Find the most recent run folder
    run_folders = [d for d in base_logs_dir.iterdir() 
                   if d.is_dir() and d.name.startswith("run_")]
    
    if not run_folders:
        return None
    
    # Sort by creation time (most recent first)
    run_folders.sort(key=lambda x: x.stat().st_ctime, reverse=True)
    return run_folders[0]


def find_latest_features_json(init_logs_dir: Path) -> Optional[Path]:
    """Find the latest Features_level_N.json file in the most recent run folder"""
    if not init_logs_dir.exists():
        return None
    
    run_folders = [d for d in init_logs_dir.iterdir() 
                   if d.is_dir() and d.name.startswith("run_")]
    
    if not run_folders:
        return None
    
    run_folders.sort(key=lambda x: x.stat().st_ctime, reverse=True)
    run_folder = run_folders[0]
    
    # Find the deepest Features_level_N.json
    level = 0
    latest_file = None
    
    while True:
        file_path = run_folder / f"Features_level_{level}.json"
        if not file_path.exists():
            break
        latest_file = file_path
        level += 1
    
    return latest_file


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


def load_level_data(level: int, run_folder: Path) -> Optional[Dict[str, Any]]:
    """Load level data from JSON file"""
    try:
        filename = f"Features_level_{level}.json"
        filepath = run_folder / filename
        
        if not filepath.exists():
            log_error(
                error_type="FILE_NOT_FOUND",
                error_message=f"Level {level} file not found",
                details=f"Expected file: {filepath}"
            )
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data
        
    except Exception as e:
        log_error(
            error_type="FILE_LOAD_ERROR",
            error_message=f"Failed to load level {level} data from JSON file",
            details=f"Source file: {filepath if 'filepath' in locals() else 'unknown'}",
            exception=e
        )
        return None


def get_run_info(run_folder: Path) -> Dict[str, Any]:
    """Get information about a run folder"""
    if not run_folder.exists():
        return {"status": "not_found"}
    
    try:
        level_files = []
        level = 0
        
        while True:
            file_path = run_folder / f"Features_level_{level}.json"
            if not file_path.exists():
                break
            
            stat = file_path.stat()
            level_files.append({
                "level": level,
                "file": file_path.name,
                "size": stat.st_size,
                "modified": stat.st_mtime
            })
            level += 1
        
        return {
            "status": "found" if level_files else "empty",
            "run_folder": run_folder.name,
            "level_files": level_files,
            "total_levels": len(level_files)
        }
        
    except Exception as e:
        log_error(
            error_type="RUN_INFO_ERROR",
            error_message=f"Failed to get run info",
            details=f"Run folder: {run_folder}",
            exception=e
        )
        return {"status": "error", "error": str(e)}


# ==================== ASYNC UTILITIES ====================

async def call_llm_api_async(llm_func, *args, **kwargs):
    """Generic async wrapper for LLM API calls"""
    semaphore = asyncio.Semaphore(get_config().llm.max_concurrent_requests)
    
    async with semaphore:
        # Run the synchronous LLM API call in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: llm_func(*args, **kwargs))


def handle_json_parsing_error(response: str, context: str) -> None:
    """Handle JSON parsing errors with context"""
    if "Unterminated string" in str(response) or "Expecting ',' delimiter" in str(response):
        log_error(
            error_type="JSON_TRUNCATION_ERROR",
            error_message="LLM response appears to be truncated due to token limit",
            details=f"Context: {context}\nResponse length: {len(response)} chars"
        )
    else:
        log_error(
            error_type="JSON_PARSE_ERROR",
            error_message="LLM did not return valid JSON",
            details=f"Context: {context}\nResponse length: {len(response)} chars"
        )


def handle_api_error(error: Exception, provider: str, model: str) -> str:
    """Handle API errors and return appropriate error type"""
    error_str = str(error)
    
    if "API key" in error_str or "ANTHROPIC_API_KEY" in error_str or "OPENAI_API_KEY" in error_str:
        return "API_KEY_ERROR"
    elif "quota" in error_str.lower() or "limit" in error_str.lower():
        return "API_QUOTA_ERROR"
    elif "timeout" in error_str.lower():
        return "API_TIMEOUT_ERROR"
    elif "network" in error_str.lower() or "connection" in error_str.lower():
        return "API_NETWORK_ERROR"
    else:
        return "GENERAL_API_ERROR"


# ==================== VALIDATION UTILITIES ====================

def validate_actor_data(actor_data: Dict[str, Any]) -> bool:
    """Validate actor data structure"""
    required_fields = ['name', 'description', 'type']
    return all(field in actor_data and actor_data[field] for field in required_fields)


def validate_generation_request(request_data: Dict[str, Any]) -> List[str]:
    """Validate generation request data"""
    config = get_config()
    errors = []
    
    # Validate provider
    if 'provider' not in request_data:
        errors.append("Provider is required")
    elif request_data['provider'] not in ['anthropic', 'openai']:
        errors.append("Provider must be 'anthropic' or 'openai'")
    
    # Validate model
    if 'model' not in request_data:
        errors.append("Model is required")
    
    # Validate numeric parameters
    if 'num_actors' in request_data:
        if not isinstance(request_data['num_actors'], int):
            errors.append("num_actors must be an integer")
        elif not (config.limits.min_actors <= request_data['num_actors'] <= config.limits.max_actors):
            errors.append(f"num_actors must be between {config.limits.min_actors} and {config.limits.max_actors}")
    
    if 'num_subactors' in request_data:
        if not isinstance(request_data['num_subactors'], int):
            errors.append("num_subactors must be an integer")
        elif not (config.limits.min_subactors <= request_data['num_subactors'] <= config.limits.max_subactors):
            errors.append(f"num_subactors must be between {config.limits.min_subactors} and {config.limits.max_subactors}")
    
    if 'target_depth' in request_data:
        if not isinstance(request_data['target_depth'], int):
            errors.append("target_depth must be an integer")
        elif not (config.limits.min_depth <= request_data['target_depth'] <= config.limits.max_depth):
            errors.append(f"target_depth must be between {config.limits.min_depth} and {config.limits.max_depth}")
    
    if 'num_params' in request_data:
        if not isinstance(request_data['num_params'], int):
            errors.append("num_params must be an integer")
        elif not (config.limits.min_params <= request_data['num_params'] <= config.limits.max_params):
            errors.append(f"num_params must be between {config.limits.min_params} and {config.limits.max_params}")
    
    return errors


# ==================== FORMATTING UTILITIES ====================

def format_duration(start_time: datetime, end_time: datetime) -> str:
    """Format duration between two datetime objects"""
    duration = end_time - start_time
    total_seconds = int(duration.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds}s"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}m {seconds}s"
    else:
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


# Export commonly used functions
__all__ = [
    'log_error',
    'log_success',
    'log_info',
    'log_warning',
    'get_run_folder_path',
    'get_latest_run_folder',
    'find_latest_features_json',
    'save_level_data',
    'load_level_data',
    'get_run_info',
    'call_llm_api_async',
    'handle_json_parsing_error',
    'handle_api_error',
    'validate_actor_data',
    'validate_generation_request',
    'format_duration',
    'format_file_size'
] 
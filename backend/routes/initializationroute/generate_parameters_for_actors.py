import sys
import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
from tqdm import tqdm

# Add the parent of 'worldmodel' to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
from worldmodel.backend.llm.llm import call_llm_api

def count_actors_recursively(actor: Dict[str, Any]) -> int:
    """
    Count the total number of actors including this one and all sub-actors recursively.
    """
    count = 1  # Count this actor
    if 'sub_actors' in actor and isinstance(actor['sub_actors'], list):
        for sub in actor['sub_actors']:
            count += count_actors_recursively(sub)
    return count

def find_latest_features_json(init_logs_dir: Path) -> Path:
    """
    Find the latest Features_level_N.json file in the most recent run folder.
    Returns the Path to the file.
    """
    run_folders = [d for d in init_logs_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
    if not run_folders:
        raise FileNotFoundError("No run folders found in init_logs.")
    run_folders.sort(key=lambda x: x.stat().st_ctime, reverse=True)
    run_folder = run_folders[0]
    # Find the deepest Features_level_N.json
    n = 0
    while True:
        f = run_folder / f"Features_level_{n}.json"
        if not f.exists():
            break
        n += 1
    if n == 0:
        raise FileNotFoundError("No Features_level_N.json files found in latest run folder.")
    return run_folder / f"Features_level_{n-1}.json"

def generate_parameters_for_actor(actor: Dict[str, Any], num_params: int, model_provider: str, model_name: str) -> List[Dict[str, Any]]:
    """
    Call LLM to generate a list of parameters for the given actor dict.
    """
    prompt = f"""
You are an expert in world modeling and data schema design. For the following actor, generate a list of {num_params} important and relevant parameters that would be most useful for simulation, analytics, or AI reasoning.
- Carefully select the parameters that are most significant for this specific actor, based on its type, name, and description.
- For each parameter, provide:
  - code_name (short, snake_case, suitable for coding)
  - name (human-readable)
  - description (1-2 sentences)
  - type (string, integer, float, boolean, document, etc.)
  - expected_value (example value or range)

Actor type: {actor.get('type')}
Actor name: {actor.get('name')}
Actor description: {actor.get('description')}

Return a JSON array of exactly {num_params} objects with these fields. Example format:
[
  {{"code_name": "example_param", "name": "Example Parameter", "description": "A short description.", "type": "float", "expected_value": "0.0 - 1.0"}},
  ...
]
"""
    response = call_llm_api(
        prompt=prompt,
        model_provider=model_provider,
        model_name=model_name,
        max_tokens=2000,
        temperature=0.3
    )
    try:
        params = json.loads(response)
        if isinstance(params, list):
            return params[:num_params]  # Only keep the requested number
        else:
            return []
    except Exception:
        print(f"❌ Failed to parse parameters for actor: {actor.get('name')}")
        print("Raw LLM output:", response)
        return []

def add_parameters_recursively(actor: Dict[str, Any], num_params: int, model_provider: str, model_name: str, pbar: tqdm = None):
    """
    Add parameters to this actor and all sub-actors recursively.
    """
    actor_name = actor.get('name', 'Unknown')
    if pbar:
        pbar.set_description(f"Processing: {actor_name}")
    
    actor['parameters'] = generate_parameters_for_actor(actor, num_params, model_provider, model_name)
    
    if pbar:
        pbar.update(1)
    
    # Recursively process sub-actors if present
    if 'sub_actors' in actor and isinstance(actor['sub_actors'], list):
        for sub in actor['sub_actors']:
            add_parameters_recursively(sub, num_params, model_provider, model_name, pbar)

def main(model_provider="anthropic", model_name="claude-3-5-sonnet-latest", num_params=20):
    # Clamp num_params
    num_params = max(1, min(100, num_params))
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent.parent
    init_logs_dir = backend_dir / "init_logs"
    features_json_path = find_latest_features_json(init_logs_dir)
    print(f"📄 Loading: {features_json_path}")
    with open(features_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Count total actors first
    actors = data.get('actors', [])
    total_actors = sum(count_actors_recursively(actor) for actor in actors)
    total_params = total_actors * num_params
    
    print(f"🔢 Total actors to process: {total_actors}")
    print(f"🔢 Total parameters to generate: {total_params}")
    print(f"🔧 Parameters per actor: {num_params}")
    print(f"🤖 Using: {model_provider}:{model_name}")
    print()
    
    # Add parameters to all actors recursively with progress bar
    with tqdm(total=total_actors, desc="Generating parameters", unit="actor") as pbar:
        for actor in actors:
            add_parameters_recursively(actor, num_params, model_provider, model_name, pbar)
    
    # Save new file
    out_path = features_json_path.parent / (features_json_path.stem + "_with_params.json")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved with parameters: {out_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate parameters for all actors and sub-actors in the latest Features_level_N.json.")
    parser.add_argument('--provider', type=str, default='anthropic')
    parser.add_argument('--model', type=str, default='claude-3-5-sonnet-latest')
    parser.add_argument('--num_params', type=int, default=20, help='Number of parameters per actor (1-100)')
    args = parser.parse_args()
    main(args.provider, args.model, args.num_params) 
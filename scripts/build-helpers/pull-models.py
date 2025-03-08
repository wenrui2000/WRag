#!/usr/bin/env python3
"""
This script reads the config.yml file and pulls the specified Ollama models.
It's used during the Docker build process for the Ollama container.
"""

import os
import yaml
import subprocess
import sys


def load_config():
    """Load configuration from the config.yml file."""
    config_file = "/config.yml"
    
    if not os.path.exists(config_file):
        print(f"Error: Config file {config_file} not found.")
        sys.exit(1)
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            return config
    except Exception as e:
        print(f"Error loading config file: {e}")
        sys.exit(1)


def pull_models(config):
    """Pull Ollama models specified in the config."""
    if not config or 'llm' not in config or 'ollama_models' not in config['llm']:
        print("No models specified in config.yml. Using default models.")
        models = ["deepseek-r1:1.5b", "deepseek-r1:7b"]
    else:
        models = config['llm']['ollama_models']
    
    # Ensure models is a list
    if not isinstance(models, list):
        if isinstance(models, str):
            models = [models]
        else:
            print("Invalid model specification in config.yml. Using default models.")
            models = ["deepseek-r1:1.5b", "deepseek-r1:7b"]
    
    print(f"Models to pull: {models}")
    
    for model in models:
        print(f"Pulling model: {model}")
        try:
            subprocess.run(["ollama", "pull", model], check=True)
            print(f"Successfully pulled model: {model}")
        except subprocess.CalledProcessError as e:
            print(f"Error pulling model {model}: {e}")
            # Continue with other models even if one fails
    
    print("Model pulling complete.")


def main():
    """Main function to run the script."""
    config = load_config()
    pull_models(config)


if __name__ == "__main__":
    main() 
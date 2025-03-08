#!/bin/bash
# Start Ollama server script for Docker container

echo "Starting Ollama setup..."

# Set environment variables to fix model path issues
export OLLAMA_MODELS="/root/.ollama/models"
export OLLAMA_ORIGINS="*"
export OLLAMA_HOST=${OLLAMA_HOST:-"0.0.0.0:11434"}

# Display environment variables for debugging
echo "Environment variables:"
echo "OLLAMA_MODELS=$OLLAMA_MODELS"
echo "OLLAMA_ORIGINS=$OLLAMA_ORIGINS"
echo "OLLAMA_HOST=$OLLAMA_HOST"

# Basic network troubleshooting
echo "Network configuration:"
ip addr show || echo "ip command not available"
hostname -I || echo "hostname command not available"
echo "DNS resolution:"
cat /etc/resolv.conf || echo "resolv.conf not available"

# Read model configuration from config.yml
if [ -f /config.yml ]; then
    echo "Reading model configuration from config.yml..."
    CONFIGURED_MODELS=$(python3 -c '
import yaml
import sys
try:
    with open("/config.yml", "r") as f:
        config = yaml.safe_load(f)
    if config and "llm" in config and "ollama_models" in config["llm"]:
        if isinstance(config["llm"]["ollama_models"], list):
            for model in config["llm"]["ollama_models"]:
                print(model)
        elif isinstance(config["llm"]["ollama_models"], str):
            print(config["llm"]["ollama_models"])
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
')
    echo "The following models should be available from the build process:"
    echo "$CONFIGURED_MODELS" | while read -r model; do
        echo "- $model"
    done
else
    echo "No config.yml found. Using default models."
    CONFIGURED_MODELS="deepseek-r1:1.5b
deepseek-r1:7b"
    echo "- deepseek-r1:1.5b"
    echo "- deepseek-r1:7b"
fi

# Start Ollama in the background to pull models
echo "Starting Ollama server in the background..."
ollama serve > /dev/null 2>&1 &
SERVER_PID=$!

# Wait for Ollama to start
echo "Waiting for Ollama server to start..."
sleep 5

# Check if models exist and pull them if they don't
echo "Checking for missing models and pulling them if necessary..."
echo "$CONFIGURED_MODELS" | while read -r model; do
    if ollama list | grep -q "$model"; then
        echo "Model $model is already available."
    else
        echo "Model $model is missing. Pulling now..."
        ollama pull "$model"
        echo "Finished pulling $model."
    fi
done

# Kill background Ollama server
kill $SERVER_PID
sleep 2

echo "Actual available models:"
ollama list

# Start Ollama service
echo "Starting Ollama server..."
exec ollama serve

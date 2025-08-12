#!/bin/bash
set -e

# Wait for Ollama server to be ready
until curl -s http://ollama:11434/api/tags | grep -q '"name":"nomic-embed-text:latest"'; do
  echo "Waiting for model 'nomic-embed-text' to be pulled in Ollama..."
  sleep 2
done

# Run Streamlit app
streamlit run app.py --server.port=8501 --server.address=0.0.0.0

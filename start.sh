#!/bin/bash
set -e

MAX_RETRIES=30
RETRY_COUNT=0

echo "🔁 Waiting for Ollama to load 'nomic-embed-text' model..."

until curl -s http://ollama:11434/api/tags | grep -q '"name":"nomic-embed-text:latest"'; do
  RETRY_COUNT=$((RETRY_COUNT+1))
  if [ "$RETRY_COUNT" -ge "$MAX_RETRIES" ]; then
    echo "❌ Timeout: Ollama model 'nomic-embed-text:latest' not available after $MAX_RETRIES retries."
    exit 1
  fi
  echo "⏳ Attempt $RETRY_COUNT: Model not ready yet..."
  sleep 2
done

echo "✅ Model 'nomic-embed-text:latest' is ready. Launching Streamlit app..."

# Run the Streamlit app
exec streamlit run app.py --server.port=8501 --server.address=0.0.0.0

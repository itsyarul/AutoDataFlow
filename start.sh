#!/bin/bash

# Start the worker in the background
echo "Starting Worker..."
python -u src/worker.py &

# Start the API in the foreground
echo "Starting API..."
uvicorn src.main:app --host 0.0.0.0 --port $PORT

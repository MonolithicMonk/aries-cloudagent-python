#!/bin/bash

# 1. Force Python to output unbuffered (logs appear immediately)
export PYTHONUNBUFFERED=1

# 2. Force colors (Uvicorn and Click will disable colors if they detect a script/pipe)
export FORCE_COLOR=1
export CLICOLOR_FORCE=1

echo "Starting ACA-Py with FastAPI (Admin v2) and Hot Reload..."
echo "Monitoring directory: ./acapy_agent"

# 3. Run watchfiles
poetry run watchfiles \
    --filter python \
    "poetry run aca-py start --arg-file .vscode/fastapi.yml" \
    ./acapy_agent
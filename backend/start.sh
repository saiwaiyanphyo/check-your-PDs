#!/bin/bash
# Run from the project root: bash backend/start.sh

cd "$(dirname "$0")"
pip install -r requirements.txt -q
uvicorn main:app --reload --host 0.0.0.0 --port 8000

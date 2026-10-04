import os
import sys
from pathlib import Path

# Ensure environment variables are set BEFORE importing the application modules.
# pydantic-settings reads env vars at import time in config.py.
os.environ["EXCHANGE_RATE_API_KEY"] = "test-primary-key"
os.environ["FASTFOREX_API_KEY"] = "test-fallback-key"

# Make the project root importable as a module root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import os
import sys
from pathlib import Path

os.environ["EXCHANGE_RATE_API_KEY"] = "test-primary-key"
os.environ["FASTFOREX_API_KEY"] = "test-fallback-key"

# Make the project root importable so `import app.main` works.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
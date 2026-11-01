import os
import sys
from pathlib import Path

# Ensure tests default to SQLite so they run instantly without external Postgres
os.environ.setdefault("DATABASE_URL", "sqlite:///./peoplepulse_test.db")
os.environ["DATABASE_URL"] = "sqlite:///./peoplepulse_test.db"

# Add backend directory to sys.path so 'app' can be imported anywhere
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

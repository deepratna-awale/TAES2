import os
import sys
import tempfile
from pathlib import Path

# Use a throwaway SQLite database so tests never touch a real Postgres instance
_db_file = Path(tempfile.mkdtemp()) / "taes2_test.db"
# Set TEST_DATABASE_URL to run against Postgres instead
os.environ["DATABASE_URL"] = os.getenv("TEST_DATABASE_URL", f"sqlite:///{_db_file}")
os.environ.setdefault("DB_CONNECT_RETRIES", "1")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

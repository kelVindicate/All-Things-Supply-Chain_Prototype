# sitecustomize.py  (runs automatically on interpreter startup)
import os, sys

# Prefer DuckDB backend for Chroma (avoids sqlite version checks)
os.environ.setdefault("CHROMA_DB_IMPL", "duckdb+parquet")
os.environ.setdefault("CREWAI_STORAGE_DIR", ".crewai_storage")
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# As a fallback, swap in a modern sqlite if anything still hits sqlite3
try:
    import pysqlite3  # wheel included via pysqlite3-binary
    sys.modules["sqlite3"] = pysqlite3
except Exception:
    pass

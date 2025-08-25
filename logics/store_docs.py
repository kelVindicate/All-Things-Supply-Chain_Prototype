import os, re, sqlite3, time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(os.getenv("USER_UPLOAD_BASE", "user_uploads")).resolve()
BASE_DIR.mkdir(parents=True, exist_ok=True)

def init_docs_schema(conn: sqlite3.Connection):
    #conn.execute("DROP TABLE IF EXISTS user_docs")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS user_docs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        title TEXT NOT NULL,
        path TEXT NOT NULL,
        mime TEXT,
        size_bytes INTEGER,
        uploaded_at TEXT NOT NULL
    )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_user_docs_user ON user_docs(username)")
    conn.commit()

def safe_filename(name: str) -> str:
    name = name.strip().replace(" ", "_")
    #keeping letters, numbers, dot, dash, and underscore
    return re.sub(r"[^A-Za-z0-9._-]", "", name) or f"file_{int(time.time())}"

def save_user_uploads(conn: sqlite3.Connection, username: str, files) -> None:
    """`files` is List[UploadedFile] from Streamlit's file_uploader."""
    user_dir = (BASE_DIR / username).resolve()
    user_dir.mkdir(parents=True, exist_ok=True)

    for f in files or []:
        data = f.read()
        if not data:
            continue
        safe = safe_filename(f.name)
        #adding time suffix to avoid collisions in documents
        out = user_dir / f"{int(time.time())}_{safe}"
        out.write_bytes(data)
        conn.execute(
            "INSERT INTO user_docs (username, title, path, mime, size_bytes, uploaded_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                username,
                f.name, 
                str(out),
                getattr(f,"type", None),
                len(data),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    conn.commit()

def list_user_docs(conn, username: str) -> list[dict]:
    cols = {c[1] for c in conn.execute("PRAGMA table_info(user_docs)").fetchall()}
    uploaded_col = "uploaded_at" if "uploaded_at" in cols else ("upload_at" if "upload_at" in cols else None)
    size_col = "size_bytes" if "size_bytes" in cols else ("size_byes" if "size_byes" in cols else None)

    select_uploaded = uploaded_col if uploaded_col else "''"
    select_size = size_col if size_col else "0"
    order_by = uploaded_col if uploaded_col else "id"

    sql = f"""
      SELECT id, title, path, mime, {select_size} AS size_bytes, {select_uploaded} AS uploaded_at
      FROM user_docs
      WHERE username = ?
      ORDER BY {order_by} DESC
    """
    rows = conn.execute(sql, (username,)).fetchall()
    return [
        {
            "id": r[0],
            "title": r[1],
            "path": r[2],
            "mime": r[3],
            "size_bytes": r[4],
            "uploaded_at": r[5],
        } for r in rows
    ]

def delete_user_docs(conn: sqlite3.Connection, username:str, ids:list[int]) -> None:
    if not ids:
        return
    #removing files from disk
    q=f"SELECT id, path FROM user_docs WHERE username=? and id IN ({','.join(['?']*len(ids))})"
    rows = conn.execute(q,(username,*ids)).fetchall()
    for _, p in rows:
        try:
            Path(p).unlink(missing_ok=True)
        except Exception:
            pass
    conn.execute(f"DELETE FROM user_docs WHERE username=? AND id IN ({','.join(['?']*len(ids))})", (username, *ids))
    conn.commit()

def load_items_bytes(conn: sqlite3.Connection, username: str, ids:list[int])-> list[dict]:
    """Return items for the pipeline: [{'title': str, 'bytes':b'...'}]"""
    if not ids:
        return[]
    q=f"SELECT title, path FROM user_docs WHERE username=? AND id IN({','.join(['?']*len(ids))})"
    rows = conn.execute(q, (username, *ids)).fetchall()
    items = []
    for title, path in rows:
        try:
            b=Path(path).read_bytes()
            items.append({"title": title, "bytes":b})
        except Exception:
            continue
    return items
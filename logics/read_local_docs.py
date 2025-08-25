import io, json, re
from pathlib import Path

def chunk_text(text: str, max_chars: int = 1200, overlap: int = 150) -> list[str]:
    text = re.sub(r"\s+", " ", (text or "")).strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        cut = text.rfind(". ", start, end)
        end = cut + 1 if cut > start + 200 else end
        chunks.append(text[start:end].strip())
        start = max(end - overlap, start + 1)
    return [c for c in chunks if c]

def _read_pdf(bytes_data: bytes) -> str:
    try:
        from pdfminer.high_level import extract_text
        return (extract_text(io.BytesIO(bytes_data)) or "")
    except Exception:
        return ""

def _read_docx(bytes_data: bytes) -> str:
    try:
        import docx
        doc = docx.Document(io.BytesIO(bytes_data))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception:
        return ""

def extract_text_from_upload(filename: str, bytes_data: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return _read_pdf(bytes_data)
    if suffix == ".docx":
        return _read_docx(bytes_data)
    # txt / md fallback
    try:
        return bytes_data.decode("utf-8", errors="ignore")
    except Exception:
        return ""

def build_local_index(uploaded_items: list[dict]) -> list[dict]:
    """
    uploaded_items: [{"title": str, "bytes": b"..."}]
    returns list of chunks: [{"doc": title, "content": chunk}]
    """
    index = []
    for item in uploaded_items:
        text = extract_text_from_upload(item["title"], item["bytes"])
        for ch in chunk_text(text):
            index.append({"doc": item["title"], "content": ch})
    return index

def local_search(index: list[dict], query: str, k: int = 5) -> dict:
    # tiny keyword scorer
    q_terms = [w for w in re.findall(r"\w+", (query or "").lower()) if len(w) > 2]
    scored = []
    for row in index:
        t = row["content"].lower()
        score = sum(t.count(w) for w in q_terms)
        if score > 0:
            scored.append((score, row))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, row in scored[:k]:
        results.append({
            "title": row["doc"],
            "date": "",
            "url": f"local://{row['doc']}",
            "extract": row["content"][:800]
        })
    return {"results": results}


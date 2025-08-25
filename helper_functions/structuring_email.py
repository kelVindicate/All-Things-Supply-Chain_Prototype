import os 
os.environ.setdefault("CHROMA_DB_IMPL", "duckdb+parquet")
os.environ.setdefault("CREWAI_STORAGE_DIR", ".crewai_storage")

import sys 
try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except Exception:
    pass

import streamlit as st
from urllib.parse import quote_plus
import feedparser
import re, html
from helper_functions.geo_normalise import geo_normalise
from typing import List

from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# <----- calling openai ---->
load_dotenv(".env")
AI_Model = os.getenv ("OPENAI_MODEL_NAME")

client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY")
)

#making query more relevant with risk terms
RISK_TERMS = [
    "port closure", "strike", "export ban", "import ban", "trade ban", "sanction", "embargo", 
    "tariff", "export control", "energy shortage", "power outage", "fuel shortage", "water shortage", "drought", "earthquake", "typhoon", "hurricane", "flood", "wildfire", "Suez", "Panama Canal", "Red Sea", "logistics bottleneck", "congestion", "container shortage", "rare earth"
]

def uniq_keep_order(items: List[str]) -> List[str]:
    seen, out = set(), []
    for x in items:
        k = x.strip().lower()
        if k and k not in seen:
            out.append(x.strip())
            seen.add(k)
    return out

def loose_json_parse(txt: str) -> dict:
    """Extract first {...} JSON block or return {}."""
    try:
        return json.loads(txt)
    except Exception:
        pass 
    m = re.search(r"\{.*\}", txt, flags=re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return {}
    return {}

def extract_article_text(url:str) -> str:
    try:
        import trafilatura
        downloaded = trafilatura.fetch_url(url, timeout =15)
        if downloaded:
            extracted = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
            if extracted and len(extracted)>200:
                return extracted
    except Exception:
        pass
    return ""

#creating a cache for 24 hours
@st.cache_data(ttl=60*60*24)
def ai_expand_industry_terms(topic: str, n_terms: int = 20) -> List[str]:
    "Return a list of terms: the original topic, synonyms, related companies, processes, and materials relevant to supply chains for that industry."
    topic = (topic or "").strip()
    if not topic:
        return []
    
    prompt = (
        "You expand a supply-chain monitoring query.\n"
        "Given an industry/topic, return a JSON object with:\n"
        '{"terms": ["..."]}\n\n'
        "Rules:\n"
        "- Include synonyms, common abbreviations, core sub-processes, key materials, and 5 to 8 representative companies. \n"
        "- Keep each term short (1 to 3 words) unless a company or phrase requires longer.\n"
        "- Avoid generic business words (e.g., market share, revenue.\n)"
        "- Focus on terms that increase recall for supply chain news.\n\n"
        f"TOPIC: {topic}\n"
        'Return on JSON, LIKE: {"terms":["...","..."]}'
    )

    try:
        resp: client.responses.create(
            model=AI_MODEL,
            input=prompt,
            temprature=0.2,
        )
        txt = (resp.output_text or "").strip()
        data = loose_json_parse(txt)
        terms = data.get("terms", [])
    except Exception:
        terms = []

    #Ensure topic and supply chain phrasing are correct
    base = [topic, f"{topic} supply chain", f"{topic} supply chains"]
    terms = base + [t for t in (terms or []) if isinstance(t,str)]
    #clean
    terms = [re.sub(r"\s+", " ", t).strip() for t in terms if t and len(t) < 60]
    return uniq_keep_order(terms)[: max(5, n_terms)]

def build_news_query_ai(topic:str, location:str | None, include_risk_terms: bool = False) -> str:
    terms = ai_expand_industry_terms(topic)
    if not terms:
        #fallback minimal query
        terms = [topic, f"{topic} supply chain", f"{topic} supply chain"]
    topic_part = " OR ".join(f'"{t}"' for t in terms)
    q = f"({topic_part})"
    if include_risk_terms:
        risk_part = " OR ".join(f'"{r}"' for r in RISK_TERMS)
        q = f"{q} AND ({risk_part})"
    if location and location.strip():
        q = f'{q} AND "{location.strip()}"'
    return q

def summarise_with_ai(text:str, topic: str="", max_words: int=60) -> str:
    if not text:
        return ""

    prompt = (
        "You are a supply chain analyst. Write a cris, factual summary for an email alert.\n"
        f"Focus on implications for {topic or 'the relevant'} supply chains if any.\n"
        f"Output <= {max_words} words, no bullets, no preamble.\n\n"
        "Text:\n" + text[:12000]
    )
    try:
        resp = client.responses.create(
            model = AI_MODEL,
            input=prompt,
        )
        ai_text = (Resp.output_text or "").strip()
        return re.sub(r"\s+", " ", ai_text)
    except Exception as e:
        print(f"Error during AI summarisation: {e}")
        return text[:max_words] + "…" if len(text) >max_words else text

def clean_summary(text:str, max_chars: int = 300) -> str:
    """strip tags, collapse whitespace, and truncate without cutting mid-word."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(re.sub(r"\s+", " ", text)).strip()
    if len(text) <= max_chars:
        return ""
    limit = max(0, max_chars - 1)
    snippet = text[:limit]
    cut = snippet.rsplit(" ", 1)[0] or snipper
    while len(cut) > limit and " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return (cut or snipper) + "…"

def to_plaintext(html_body: str) -> str:
    """Very simply HTML→text fallback."""
    txt = re.sub(r"<[^>]+>",  " ", html_body)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

def fetch_news_rss(key_industry: str, free_text_location: str = None, max_items: int = 10, use_ai: bool = True, ai_max_items: int = 10, include_risk_terms: bool = True) -> list:
    #build query and url
    query = build_news_query_ai(key_industry, free_text_location, include_risk_terms=include_risk_terms)

    rss_url = f"https://news.goodle.com/rss/search?q={quote_plus(query)}&hl=en-SG&gl=SG&ceid=SG:en"

    feed = feedparser.parse(rss_url)
    news_items = []
    for idx, entry in enumerate(feed.entries[:max_items], start=1):
        #prefer cleaned summary and falls back to news content if present
        raw_summary = getattr(entry, "summary", "") or ""
        if not raw_summary and getattr(entry, "content", None):
            try:
                raw_summary - entry.content[0].value
            except Exception:
                pass

        cleaned = clean_summary(raw_summary, max_chars=300)

        ai_summary = ""
        if use_ai and idx <=ai_max_items:
            article_text = extract_article_text(getattr(entry, "link", "")) or cleaned or getattr(entry, "title", "")
            ai_summary = summarise_with_ai(article_text, topic=key_industry, max_words=60)

        news_items.append({
            "title": getattr(entry, "title" ""),
            "link": getattr(entry, "link", ""),
            "summary": clean_summary(raw_summary, max_chars=300),
            "ai_summary": ai_summary,
            "published": getattr(entry, "published", "")
        })
    return news_items


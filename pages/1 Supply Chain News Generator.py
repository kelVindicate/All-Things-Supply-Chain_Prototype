import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from openai import OpenAI
from dotenv import load_dotenv
import os
import json

from urllib.parse import quote_plus
import feedparser
import re, html

import pandas as pd
import numpy as np
import sqlite3
import secrets
import datetime
from datetime import datetime, timedelta, timezone
from typing import List


from authentication import check_password
from auth_hardcoded import login_form, require_login, logout_button
from helper_functions.geo_normalise import geo_normalise
# <---- User LOGIN ----->
if not st.session_state.get("logged_in"):
    login_form()
    st.stop()

require_login()

st.sidebar.write(f"Signed in as: {st.session_state ['user']['name']}")
logout_button()

# <----- calling openai ---->
load_dotenv(".env")
AI_MODEL = os.getenv ("OPENAI_MODEL_NAME")

client = OpenAI(
    api_key = os.getenv("OPENAI_API_KEY")
)

# setting up sqlite3 to store user data
conn = sqlite3.connect("user_data.db", check_same_thread=False)
conn.execute (
    '''
    CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
    name TEXT,
    key_industry TEXT,
    free_text_location TEXT, 
    confirmed INTEGER DEFAULT 1,
    token TEXT,
    active INTEGER DEFAULT 1
    )
    '''
)
conn.commit()
#helper functions
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
        resp = client.responses.create(
            model=AI_MODEL,
            input=prompt,
            temperature=0.2,
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
        ai_text = (resp.output_text or "").strip()
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
    cut = snippet.rsplit(" ", 1)[0] or snippet
    while len(cut) > limit and " " in cut:
        cut = cut.rsplit(" ", 1)[0]
    return (cut or snippet) + "…"

def to_plaintext(html_body: str) -> str:
    """Very simply HTML→text fallback."""
    txt = re.sub(r"<[^>]+>",  " ", html_body)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt

def fetch_news_rss(key_industry: str, free_text_location: str = None, max_items: int = 10, use_ai: bool = True, ai_max_items: int = 10, include_risk_terms: bool = True) -> list:
    #build query and url
    query = build_news_query_ai(key_industry, free_text_location, include_risk_terms=include_risk_terms)

    rss_url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-SG&gl=SG&ceid=SG:en"

    feed = feedparser.parse(rss_url)
    news_items = []
    for idx, entry in enumerate(feed.entries[:max_items], start=1):
        #prefer cleaned summary and falls back to news content if present
        raw_summary = getattr(entry, "summary", "") or ""
        if not raw_summary and getattr(entry, "content", None):
            try:
                raw_summary = entry.content[0].value
            except Exception:
                pass

        cleaned = clean_summary(raw_summary, max_chars=300)

        ai_summary = ""
        if use_ai and idx <=ai_max_items:
            article_text = extract_article_text(getattr(entry, "link", "")) or cleaned or getattr(entry, "title", "")
            ai_summary = summarise_with_ai(article_text, topic=key_industry, max_words=60)

        news_items.append({
            "title": getattr(entry, "title", ""),
            "link": getattr(entry, "link", ""),
            "summary": clean_summary(raw_summary, max_chars=300),
            "ai_summary": ai_summary,
            "published": getattr(entry, "published", "")
        })
    return news_items
#email content
def create_email_content(name, key_industry, free_text_location):
    subject = f"{key_industry} Updates"

    raw = (free_text_location or "").strip()
    normalised_loc = None
    if raw:
        normalised_loc =geo_normalise(raw)
        if isinstance(normalised_loc, dict):
          normalised_loc = (
            normalised_loc.get("canonical_name")
            or normalised_loc.get("name")
            or raw
          )

    news_items = fetch_news_rss(key_industry, normalised_loc, max_items=10, include_risk_terms=True)

#Build HTML
    header_loc = f" • Focus region: {html.escape(normalised_loc)}" if normalised_loc else ""
    if not news_items:
        items_html = '<tr><td style="padding:12px 0; color:#444">No recent items found.</td></tr>'
    else:
        rows = []
        for it in news_items:
            title = html.escape(it["title"])
            link = it["link"]
            published = html.escape(it["published"])
            ai_or_clean = it.get("ai_summary") or it.get("summary") or ""
            summary = html.escape(ai_or_clean) if ai_or_clean else "-"
            rows.append(
                f"""
                <tr>
                  <td style="padding:12px 0;border-bottom:1px solid #eee">
                    <div style="font-weight:600;margin-bottom:4px;">
                      <a href="{link}" style="color:#0b57d0;text-decoration:none">{title}</a>
                    </div>
                    <div style="font-size:12px;color:#666;margin-bottom:6px;">{published}</div>
                    <div style="font-size:14px;line-height:1.45;color:#333">{summary}</div>
                    <div style="margin-top:6px">
                      <a href="{link}" style="font-size:13px;color:#0b57d0;">Open article</a>
                    </div>
                  </td>
                </tr>
                """
            )
        items_html = "\n".join(rows)

    body = f"""
    <!doctype html>
    <html>
      <body style="margin:0;padding:0;background:#f6f8fb">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f6f8fb;padding:24px 0">
          <tr>
            <td align="center">
              <table role="presentation" width="640" cellspacing="0" cellpadding="0" style="background:#ffffff;border-radius:10px;padding:24px; font-family:Arial,Helvetica,sans-serif">
                <tr>
                  <td>
                    <h2 style="margin:0 0 4px 0; font-size:20px;color:#111">Hello {html.escape(name)},</h2>
                    <div style="margin:0 0 14px 0; font-size:14px;color:#333">
                      Here are the latest updates in <strong>{html.escape(key_industry)}</strong>{header_loc}.
                    </div>
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                      {items_html}
                    </table>
                    </div>
                    <div style="margin-top:24px;font-size:14px;color:#333">
                      Best regards,
Your News Alert Service
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """
    return subject, body

def send_email(email, subject, body):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = st.secrets["smtp_email"]
    password = st.secrets["smtp_password"]

    message = MIMEMultipart("alternative")
    message['From'] = f'News Alert <{sender_email}>'
    message['To'] = email
    message['Subject'] = subject

    alt_text = to_plaintext(body)
    message.attach(MIMEText(alt_text, 'plain'))
    message.attach(MIMEText(body, 'html'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, password)
        server.sendmail(sender_email, email, message.as_string())
#UI configuration
st.title("Supply Chain News Generator")
with st.form("Subscribe"):
    name = st.text_input ("Enter your name:")
    email = st.text_input ("Enter your email:")
    key_industry = st.selectbox("Select your key industry:", ["Agriculture", "Biomedical", "Pharmaceutical", "Electronics", "Energy", "Oil", "Construction", "General Manufacturing", "Precision Engineering", "Air Transport", "Sea Transport", "Land Trandport"])
    free_text_location = st.text_input("Enter location (optional):", value="United States")
    submitted = st.form_submit_button("Generate news")

if submitted:
    if not email or "@" not in email:
        st.error("Invalue email address.")
    else:
        conn.execute('''
        insert into users (email, name, key_industry, free_text_location, confirmed, token, active)
        values (?, ?, ?, ?, 1, NULL, 1)
        on conflict (email) do update set
            name = excluded.name, 
            key_industry = excluded.key_industry,
            free_text_location = excluded.free_text_location, 
            confirmed = excluded.confirmed,
            token = excluded.token,
            active = excluded.active
        ''', (email, name, key_industry, free_text_location))
        conn.commit()

        subject, body = create_email_content(name, key_industry, free_text_location)
        try:
            send_email(email, subject, body)
            st.success("News generated successfully! Please check your inbox or spam for news!")
        except Exception as e:
            st.error(f"Failed to send email: {e}")
import os 
os.environ.setdefault("CHROMA_DB_IMPL", "duckdb+parquet")
os.environ.setdefault("CREWAI_STORAGE_DIR", ".crewai_storage")

import sys 
try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except Exception:
    pass
import os
import json
from typing import Optional, TypedDict
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv(".env")

class GeoResult(TypedDict, total=False):
    canonical_name: str
    place_type: Optional[str]
    iso_country_code: Optional[str]
    notes: Optional[str]

def _fallback(query: str) -> GeoResult:
    q = (query or "").strip()
    if not q:
        return {"canonical_name": ""}

def geo_normalise(query: str) -> GeoResult:
    from crewai import Agent, Task, Crew
    """
    Normalises a geographical query to a canonical form.
    
    Args:
        query (str): The geographical query to normalise.
        
    Returns:
        GeoResult: A dictionary containing the canonical name, place type, and optional ISO country code.
    """
    input = {"geographical_query": query}
    print(input)
    agent_geo_normaliser = Agent(
        role="Geo Normaliser",
        goal="Normalise the {geographical_query} into a canonical form.",
        backstory=("You are an expert in geographical normalisation."
                   "Your task is to take a geographical query and identify the most likely real-world place the user is referring to."
                   "You will normalise the place name to its canonical form, including any common abbreviations."),
        tools=[],
        verbose=True
    )
    
    task_geo_normaliser = Task(
        description="""
                    1. Take the geographical query and identify the most likely real-world place the user is referring to.
                    2. Normalise the place name to its canonical form, including any common abbreviations. Prefer widely-recognised names.
                    3. If ambiguous, pick the most globally common interpretation and note ambiguity in 'notes'.
                    4. return a strict json object with these keys only: canonical name (string, required), place type (string, optional), ISO country code (string, optional) and notes(string, optional; include ambiguity notes if any).
                """,
        expected_output= '{"canonical_name": "string", "place_type": "string", "iso_country_code": "string", "notes": "string"}',
        agent=agent_geo_normaliser
    )
    
    crew = Crew(agents=[agent_geo_normaliser],
                tasks =[task_geo_normaliser])

    try:
        result = crew.kickoff(inputs={"geographical_query": query})
        print(f"Result from geo normaliser: {result}")
        raw = getattr(result, "raw", None)
        if not raw and hasattr(result, "tasks_output"):
            outs = getarr(result, "tasks_ooutput", [])
            if outs:
                raw = getattr(outs[0], "raw", None) or getattr (outs[0], "output", None)
        if not isinstance(raw, str):
            raw = str(raw) if raw is not none else ""  

        data = json.loads(raw)

        if not isinstance(data, dict):
            return _fallback(query)

        canonical_name = data.get("canonical_name") or query
        place_type = data.get ("place_type")
        iso_country_code = data.get("iso_country_code")
        notes = data.get("notes")

        result_dict: GeoResult = {
            "canonical_name": str(canonical_name),
        }
        if place_type is not None:
            result_dict["place_type"] = str(place_type)
        if iso_country_code is not None:
            result_dict["iso_country_code"] = str(iso_country_code)
        if notes is not None:
            result_dict["notes"] = str(notes)
        print(f"Normalised query '{query}' to {result_dict}")
        return result_dict
    except Exception as e:
        print(f"Error normalising query '{query}': {e}")
        return _fallback(query)
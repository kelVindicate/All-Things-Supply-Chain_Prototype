import os 
os.environ.setdefault("CHROMA_DB_IMPL", "duckdb+parquet")
os.environ.setdefault("CREWAI_STORAGE_DIR", ".crewai_storage")

import sys 
try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except Exception:
    pass

# <---Libraries--->
import os
from crewai import Agent, Task, Crew, Process
from local_tools.directory_search_tool import DirectorySearchTool

from dotenv import load_dotenv

from pathlib import Path

load_dotenv(".env")
os.environ.setdefault("CHROMA_CLIENT_TYPE", "persistent")
os.environ.setdefault("CHROMA_PERSIST_PATH", ".chroma")

# <---Prompt Engineering--->
agent_prompt_engineer = Agent(role = "Prompt Engineer",
                              goal = """
                              Refine the {user_query} about Ceranum's supply chain resilience so that it becomes a context-rich and structured retrieval prompt.
                              The refined prompt should explicitly capture entities, commodities or critical supplies, time horizons, risks types, and intended outcomes.""",
                              backstory = """
                              Specialist in turning open-ended questions into precise and high-signal prompts for RAG.
                              Understand supply chain resilience strategies and how these map to queries.""",
                              allow_delegation = False,
                              verbose = True)

task_prompt_engineering = Task(description = """
                               1) Read the {user_query}.
                               2) Identify and clarify missing dimensions needed for high-quality retrieval:
                               - Who/Where: Ceranum agencies, domestic industries, potential partners like companies and countries etc.
                               - What: Critical supplies or technologies, chokepoints, standards or regulations, financing and policy tools etc.
                               - When: Relevant time windows
                               - Risks: Geopolitical, logistics, climate, energy, cyber, supplier concentration, compliance etc.
                               - Outcome: Actions and/or insights such as due diligence requirements, and partnership prospects prevailing positions etc.
                               3) Write a single optimised retrieval prompt that includes constraints, entities, and synonyms.
                               4) Provide three semantically diverse alternative phrasings oriented to (a) policy and strategy, (b) logistics and operations, and (c) deals and partnerships.
                               5) List high-signal keywords and synonyms like commodity aliases or HS codes.
                               6) List ambiguities or assumptions, and how to disambiguate if needed.

                               Return a Markdown brief in markdown with these sections:
                               - Optimised Retrieval Prompt: A single paragraph prompt fit for RAG
                               - Variations: Three bullet points repressenting a meaningfully different phrasing of the query (policy and strategy, logistics and operations, and deals and partnerships)
                               - Keywords: A bulleted list of key terms and synonyms, including commodity aliases
                               - Context and Definitions: A bulleted list of acronyms, definitions, or domaint context
                               - Assumptions: A bulleted list of assumptions and how to disambiguate if needed""",
                               expected_output = """
                               A Markdown brief with only the following sections:
                               - Optimised Retrieval Prompt,
                               - Variations,
                               - Keywords,
                               - Context and Definitions,
                               - Assumptions""",
                               agent = agent_prompt_engineer)

# <---Research--->
agent_researcher = Agent(role = "Researcher",
                         goal = """
                         Using the Prompt Engineer's brief, retrieve only the most relevant verbatim snippets from the repository.
                         These should be related to Ceranum's supply chain resilience interests, priorities, and potential collaboration opportunities""",
                         backstory = "Detail-oriented and precise researcher that extracts minimal necessary text, and always attributes exact verifiable citations so that the Analyst can synthesise confidently",
                         allow_delegation = False,
                         verbose = True)

task_research = Task(description = """
                     1) Use DirectorySearchTool to search the repository.
                     2) Extract verbatim snippers relevant to the prompt. Prioritise:
                     - Ceranum-specific references or analogues from comparable nations
                     - Critical supplies, supplier concentration, chokepoints, and alternative sources
                     - Instruments such as policy levers, standards or certifications, incentives, financing, trade tools etc.
                     - Partnership and collaboration leads such as companies, countries, initiatives, MOUs, FTAs, etc.
                     - Constraints and risks such as regulatory, ESG, logistics, geopolitical, cyber, climate etc.
                     3) For each snippet, include a precise citation in the format: "file_name", file_name.<page_number>.
                     4) Avoid duplicate or near-duplicate quotes.
                     5) If nothing is found for a sub-topic, state that explicitly.

                     Return a Markdown report with these sections
                     - Thematic Findings: A bulleted list of snippets categorised according to common topics, with their respective citations.
                     - Source Index: A table listing the source file, pages or sections referenced, and brief notes on relevance""",
                     expected_output = """
                     A Markdown research report with only the following sections:
                     - Thematic Findings
                     - Source Index""",
                     agent = agent_researcher)
task_research.context = [task_prompt_engineering]

# <---Analysing--->
agent_analyst = Agent(
    role = "Analyst",
    goal = """
    Synthesise the Researcher's report into concise, contextual, and actionable insights that answer the {user_query}, guided by the optimised retrieval prompt provided by the Prompt Engineer.
    The answer should reflect Ceranum's supply chain resilience interests and priorities.""",
    backstory = "Turn evidence into decisions, by highlighting what matters for Ceranum, the trade-offs, and concrete next steps",
    allow_delegation = False,
    verbose = True
)

task_analyse = Task(
    description = """
    1) Read the optimised retrieval prompt, followed by the thematic findings and source index.
    2) Produce a decision-ready synthesis tailored to Ceranum:
    - Executive Summary: A 5-8 sentence answer to {user_query}
    - Ceranum Priorities: What the sources imply for Ceranum, such as constraints, interests, timings, etc.
    - Collaboration Opportunities: Specific partner companies, countries, and intiaitives, the expected value of such collaboration, as well as what Ceranum is expected to bring (data sharing, financing, policy, standards etc.)
    - Gaps and Risks: Key uncertainities, compliance or ESG issues, chokepoints not covered, data gaps, etc.
    - Recommendations: 5-8 actionable and specific steps
    - References: A bibliography mapping references to the exact snippet.
    3) Keep claims tightly grounded in the Researcher's citations. Highlight any inference as "inference" if not directly quoted.
    4) Be concise and structured.""",
    expected_output = """A well-structured brief including:
    - Executive Summary
    - Ceranum Priorities
    - Collaboration Opportunities
    - Risks & Gaps
    - Recommendations
    - References""",
    agent = agent_analyst
)
task_analyse.context = [task_prompt_engineering, task_research]



def build_crew(repository: Path) -> Crew:
    if not repository.exists() or not repository.is_dir():
        raise FileNotFoundError(f"Working repository not found.")
    
    tool_researcher = DirectorySearchTool(directory = str(repository))
    agent_researcher.tools = [tool_researcher]

    return Crew(agents = [agent_prompt_engineer, agent_researcher, agent_analyst],
                tasks = [task_prompt_engineering, task_research, task_analyse],
                process = Process.sequential,
                verbose = True,
                max_execution_time = 200)

# ---- Runner ----
def process_qna(user_query: str, repository_path: str | Path = "repository_working"):
    repo_path = Path(repository_path)
    crew = build_crew(repo_path)
    result = crew.kickoff(inputs={"user_query": user_query})
    # return the last task's raw output (same as your original intention)
    return result.tasks_output[-1].raw
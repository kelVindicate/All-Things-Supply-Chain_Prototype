import os
os.environ["CREWAI_DISABLE_TELEMETRY"] = "true"

import streamlit as st
from crewai import Agent, Task, Crew

st.title("CrewAI Healthcheck")

# Define agent
agent = Agent(
    role="Greeter",
    goal="Say hi and stop.",
    backstory="A friendly agent.",
    verbose=True,
    allow_delegation=False,
    llm="gpt-4o-mini"
)

# Define task
task = Task(description="Say hello in one short sentence")

# Create crew
crew = Crew(agents=[agent], tasks=[task])

# Run button
if st.button("Run"):
    try:
        result = crew.kickoff()
        st.success(result)
    except Exception as e:
        st.error(repr(e))
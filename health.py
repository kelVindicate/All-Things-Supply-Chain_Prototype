import os
os.environ[“CREWAI_DISABLE_TELEMETRY”]=”true”
import streamlit as st
st.title(“CrewAI Healthcheck”)
from crewai import Agent, Task, Crew
agent=Agent(
              role=”Greeter”,
              goal=”Sayhi and stop.”,
              backstory=”A
friendly agent.”,
              verbose=True,
              allow_delegation=False,
              llm=”gpt-4o=mini”
)
Task=Task(description=”Say hello in one short sentence”)
Crew=Crew(agents=[agent],tasks=[task])
If st.button(“Run”):
              try:
                            result=crew.kickoff()
                             st.success(result)
              except:Exception as e:
                             st.error(repr(e))
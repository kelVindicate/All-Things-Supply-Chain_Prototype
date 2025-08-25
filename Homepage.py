import sys 
try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except Exception:
    pass

# <---Changelog--->
# 11/08/25: Implemented Streamlit

# <---Libraries--->
import streamlit as st

# <---Homepage Design--->
st.title(f"Welcome to Supply Chain Tool!")
st.image("assets/wallpaper.png",
         use_container_width = True)
st.write("""IMPORTANT NOTICE: This web application is developed as a proof-of-concept prototype. The information provided here is NOT intended for actual usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.
Furthermore, please be aware that the LLM may generate inaccurate or incorrect information. You assume full responsibility for how you use any generated output.
Always consult with qualified professionals for accurate and personalized advice.""")
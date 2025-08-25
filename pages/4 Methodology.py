import sys 
try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
except Exception:
    pass

import streamlit as st

st.title("Methodology")
st.image("assets/Methodology.png",
         use_container_width = True)
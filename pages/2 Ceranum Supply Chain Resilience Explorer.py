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
import streamlit as st
from auth_hardcoded import login_form, require_login, logout_button
from helper_functions.repository import prepare_repository, list_user_uploads, get_user_repository
from logics.crew_qna import process_qna

# <-----User Login------>
st.set_page_config(page_title="App", page_icon="🔐")

if not st.session_state.get("logged_in"):
    login_form()
    st.stop()

require_login()  # or require_login(roles=["admin"])

st.sidebar.write(f"Signed in as: {st.session_state['user']['name']}")
logout_button()

# <---User Key--->
user = st.session_state["user"]
user_key = user.get("id") or user.get("name") # Get the user's key to access the correct user folder

# <---Streamlit App Configuration-->
st.title("Ceranum Supply Chain Resilience Explorer")

st.subheader("Ingest Documents")
files = st.file_uploader("Upload documents",
                         type = ["docx", "md", "pdf", "txt"],
                         accept_multiple_files = True)

files_existing = [path.name for path in list_user_uploads(user_key)] # Existing user uploads
files_selection = st.multiselect("Select which uploaded documents to include in this request:",
                                 options = files_existing,
                                 default = files_existing,
                                 help = "Uploads are saved under your account. Only selected files will be ingested into the request.") # Allows users to decide which user upload to use in request

if st.button("Build Repository"):
    repository_path = prepare_repository(files, user_key = user_key, selected_file_names = files_selection)
    st.session_state["repository_status"] = True
    st.success(f"Working repository is ready.")

form = st.form(key = "form")
form.subheader("Explore collaboration paths, opportunities, and vulnerabilities in Ceranum's supply chain resilience")
user_query = form.text_area("What supply chain resilience collaboration, query, or collaboration do you want to explore for Ceranum?",
                            height = 200)

if form.form_submit_button("Submit"):
    if not st.session_state.get("repository_status", False):
        repository_path = prepare_repository(files or [], user_key = user_key, selected_file_names = files_selection or [])
        st.session_state["repository_status"] = True
    
    st.toast(f"Question: {user_query}")
    response = process_qna(user_query, repository_path = str(get_user_repository(user_key)))
    st.write(response)
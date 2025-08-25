import bcrypt
import streamlit as st

USERS = {
    "davina": {
        "name": "davina",
        "role": "admin",
        "pw_hash": "$2b$12$G3lwyUANvSyVtTwTyNDN/OI3h7Dph40XxRp2NgUCwRTGnOE4d2/1e", #hello,world!
    },
    "kelvin": {
        "name": "kelvin",
        "role": "user",
        "pw_hash": "$2b$12$v0GUz7.JBgpwolO0YuAr1.5Sg9XgzyoXkw24I2tZOAJrNgT0N49nW", #tired...
    },
    "chin": {
        "name": "chin",
        "role": "user",
        "pw_hash": "$2b$12$v0GUz7.JBgpwolO0YuAr1.5Sg9XgzyoXkw24I2tZOAJrNgT0N49nW", #shrimpy
    }
}

def verify_password(plain: str, pw_hash:str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), pw_hash.encode("utf-8"))
    except Exception:
        return False

def login_form():
    with st.form("LOGIN", clear_on_submit=False):
        st.subheader("Log in")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Log in")

    if not submit:
        return
    
    key = (username or "").strip().lower()
    user = USERS.get(key)
    if not user or not verify_password(password, user["pw_hash"]):
            st.error("Invalid username or password.")
            return

    st.session_state["logged_in"] = True
    st.session_state["user"] = {
        "username": key,
        "name":user.get("name",key),
        "role": user.get("role","user"),
    }
    st.success(f"Welcome, {st.session_state['user']['name']}:)")
    st.rerun()

def require_login(roles=None):
    if not st.session_state.get("logged_in"):
        st.stop()
    if roles and st.session_state["user"]["role"] not in roles:
        st.error("You don't have access to this page.")
        st.stop()

def logout_button():
    if st.sidebar.button("Log out", use_container_width = True):
        st.session_state.clear()
        st.rerun()
import streamlit as st
from streamlit_app.api_client import APIClient
from streamlit_app.components.sidebar import render_sidebar
from streamlit_app.components.chat_view import render_chat_view

st.set_page_config(
    page_title="ATS AI - Recruiter Chat",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

def main():
    client = APIClient()
    render_sidebar(client)
    render_chat_view(client)

if __name__ == "__main__":
    main()

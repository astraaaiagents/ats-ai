import streamlit as st
from streamlit_app.api_client import APIClient

STARTER_PROMPTS = [
    {"title": "🎯 Source Candidates", "prompt": "Source top 5 Java engineers with AWS experience"},
    {"title": "📊 Pipeline Review", "prompt": "Review candidate fit scores for open positions"},
    {"title": "✉️ Draft Outreach", "prompt": "Draft personalized outreach emails for top candidates"},
]

def _navigate_to_chat():
    """Helper to request active portal tab switch to Conversations & Chat view."""
    st.session_state["switch_tab"] = "💬 Conversations"
    st.session_state["view_mode"] = "chat"

def render_sidebar(client: APIClient):
    """Render sidebar with session history and new conversation trigger."""
    st.sidebar.title("🤖 AI Recruiter Agent")
    st.sidebar.caption("Recruiter Gateway Portal")

    if st.sidebar.button("➕ New Conversation", use_container_width=True, type="primary"):
        st.session_state["session_id"] = None
        st.session_state["messages"] = []
        _navigate_to_chat()
        st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Quick Starters")

    for starter in STARTER_PROMPTS:
        if st.sidebar.button(starter["title"], key=f"starter_{starter['title']}", use_container_width=True):
            st.session_state["session_id"] = None
            st.session_state["messages"] = []
            st.session_state["pending_prompt"] = starter["prompt"]
            _navigate_to_chat()
            st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Recent Conversations")

    sessions = client.get_sessions(limit=25)

    if not sessions:
        st.sidebar.info("No active conversation history")

    active_sid = st.session_state.get("session_id")
    current_tab = st.session_state.get("nav_tab")

    for s in sessions:
        sid = s["id"]
        title = s.get("title") or f"Session {sid[:8]}"
        is_active = active_sid == sid and current_tab == "💬 Conversations"
        btn_label = f"💬 {title[:20]}" if not is_active else f"👉 {title[:20]}"

        col_chat, col_del = st.sidebar.columns([4, 1])
        with col_chat:
            if st.button(btn_label, key=f"session_{sid}", use_container_width=True):
                st.session_state["session_id"] = sid
                history = client.get_conversation_history(sid)
                st.session_state["messages"] = [
                    {
                        "role": msg.get("role", "assistant"),
                        "content": msg.get("content", ""),
                        "cards": msg.get("cards", []),
                    }
                    for msg in history
                ] if history else []
                _navigate_to_chat()
                st.rerun()

        with col_del:
            if st.button("🗑️", key=f"del_sidebar_{sid}", help="Delete conversation"):
                client.delete_conversation(sid)
                if st.session_state.get("session_id") == sid:
                    st.session_state["session_id"] = None
                    st.session_state["messages"] = []
                st.rerun()

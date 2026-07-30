import streamlit as st
from streamlit_app.api_client import APIClient

STARTER_PROMPTS = [
    {"title": "🎯 Source Candidates", "prompt": "Source top 5 Java engineers with AWS experience"},
    {"title": "📊 Pipeline Review", "prompt": "Review candidate fit scores for open positions"},
    {"title": "✉️ Draft Outreach", "prompt": "Draft personalized outreach emails for top candidates"},
]

def render_sidebar(client: APIClient):
    """Render sidebar with session history and new conversation trigger."""
    st.sidebar.title("🤖 AI Recruiter Agent")
    st.sidebar.caption("Recruiter Gateway Portal")

    if st.sidebar.button("➕ New Conversation", use_container_width=True, type="primary"):
        st.session_state["session_id"] = None
        st.session_state["messages"] = []
        st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Quick Starters")

    for starter in STARTER_PROMPTS:
        if st.sidebar.button(starter["title"], key=f"starter_{starter['title']}", use_container_width=True):
            st.session_state["session_id"] = None
            st.session_state["messages"] = []
            st.session_state["pending_prompt"] = starter["prompt"]
            st.rerun()

    st.sidebar.divider()
    st.sidebar.subheader("Recent Conversations")

    logs = client.get_action_log(limit=20)
    seen_sessions = set()
    sessions = []

    for log in logs:
        sid = log.get("session_id")
        if sid and sid not in seen_sessions:
            seen_sessions.add(sid)
            sessions.append({
                "id": sid,
                "label": f"Session {sid[:8]}...",
                "time": str(log.get("created_at", ""))[:10],
            })

    if not sessions:
        st.sidebar.info("No active conversation history")

    for s in sessions:
        is_active = st.session_state.get("session_id") == s["id"]
        btn_label = f"💬 {s['label']}" if not is_active else f"👉 {s['label']}"
        if st.sidebar.button(btn_label, key=f"session_{s['id']}", use_container_width=True):
            st.session_state["session_id"] = s["id"]
            history = client.get_conversation_history(s["id"])
            st.session_state["messages"] = [
                {
                    "role": msg.get("role", "assistant"),
                    "content": msg.get("content", ""),
                    "cards": msg.get("cards", []),
                }
                for msg in history
            ]
            st.rerun()

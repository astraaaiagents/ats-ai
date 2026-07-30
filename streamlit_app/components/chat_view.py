import streamlit as st
from streamlit_app.api_client import APIClient
from streamlit_app.components.cards import (
    render_candidate_card,
    render_job_card,
    render_alert_card,
)

def render_chat_view(client: APIClient):
    """Render conversation list or active chat session view."""
    if "view_mode" not in st.session_state:
        if st.session_state.get("session_id") or st.session_state.get("messages") or st.session_state.get("pending_prompt"):
            st.session_state["view_mode"] = "chat"
        else:
            st.session_state["view_mode"] = "list"

    # Pending prompt or explicit session selection automatically switches to chat view
    if st.session_state.get("pending_prompt") or st.session_state.get("session_id"):
        st.session_state["view_mode"] = "chat"

    if st.session_state["view_mode"] == "list":
        _render_sessions_list_view(client)
    else:
        _render_active_chat_view(client)

def _render_sessions_list_view(client: APIClient):
    """Render recent conversations list view."""
    col_title, col_new = st.columns([3, 1])
    with col_title:
        st.header("💬 Recent Conversations")
        st.caption("Select a conversation to view chat history or start a new conversation.")
    with col_new:
        st.write("")
        if st.button("➕ New Conversation", type="primary", use_container_width=True):
            st.session_state["session_id"] = None
            st.session_state["messages"] = []
            st.session_state["view_mode"] = "chat"
            st.rerun()

    sessions = client.get_sessions(limit=50)

    if not sessions:
        st.info("No recent conversation history found. Click '➕ New Conversation' to start your first chat!")
        return

    st.write(f"Showing **{len(sessions)}** recent conversation session(s):")

    for s in sessions:
        sid = s["id"]
        title = s.get("title") or "Conversation"
        created = str(s.get("created_at", ""))[:16].replace("T", " ")

        with st.container(border=True):
            col_info, col_btn = st.columns([4, 1])
            with col_info:
                st.markdown(f"**💬 {title}**")
                st.caption(f"🆔 `{sid[:8]}...` • 🕒 {created if created else 'Recent'}")
            with col_btn:
                if st.button("💬 Open Chat", key=f"list_open_{sid}", type="secondary", use_container_width=True):
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
                    st.session_state["view_mode"] = "chat"
                    st.rerun()

def _render_active_chat_view(client: APIClient):
    """Render active chat view with SSE streaming and history."""
    col_nav, col_new = st.columns([3, 1])
    with col_nav:
        if st.button("⬅️ Back to Conversations List"):
            st.session_state["view_mode"] = "list"
            st.rerun()
    with col_new:
        if st.button("➕ New Conversation", type="primary", use_container_width=True):
            st.session_state["session_id"] = None
            st.session_state["messages"] = []
            st.session_state["view_mode"] = "chat"
            st.rerun()

    sid = st.session_state.get("session_id")
    st.caption(f"Active Session: `{sid}`" if sid else "Active Session: New Conversation")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Display message history
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            for card in msg.get("cards", []):
                ctype = str(card.get("type", "")).lower()
                if "candidate" in ctype:
                    render_candidate_card(card)
                elif "job" in ctype:
                    render_job_card(card)
                elif "alert" in ctype:
                    render_alert_card(card)

    # Check for pending starter prompt
    pending_prompt = st.session_state.pop("pending_prompt", None)
    prompt = st.chat_input("Ask AI Recruiter...") or pending_prompt

    if prompt:
        # Save and display user message
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Stream assistant response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            full_response = ""
            received_cards = []

            session_id = st.session_state.get("session_id")

            for event in client.stream_conversation(prompt, session_id=session_id):
                ev_type = event.get("event")
                data = event.get("data", {})

                if ev_type == "message_start" and isinstance(data, dict):
                    st.session_state["session_id"] = data.get("session_id")
                elif ev_type == "content":
                    content_chunk = data.get("content", "") if isinstance(data, dict) else str(data)
                    full_response += content_chunk
                    message_placeholder.markdown(full_response + "▌")
                elif ev_type == "card" and isinstance(data, dict):
                    received_cards.append(data)
                    ctype = str(data.get("type", "")).lower()
                    if "candidate" in ctype:
                        render_candidate_card(data)
                    elif "job" in ctype:
                        render_job_card(data)
                    elif "alert" in ctype:
                        render_alert_card(data)

            message_placeholder.markdown(full_response)

            st.session_state["messages"].append({
                "role": "assistant",
                "content": full_response,
                "cards": received_cards,
            })

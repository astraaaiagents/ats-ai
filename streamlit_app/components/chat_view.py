import streamlit as st
from streamlit_app.api_client import APIClient
from streamlit_app.components.cards import (
    render_candidate_card,
    render_job_card,
    render_alert_card,
)

def render_chat_view(client: APIClient):
    """Render main chat messages and handle prompt submission."""
    st.title("Conversations & Chat")
    st.caption("Interact with your AI Recruiter Agent for candidate sourcing, pipeline management, and outreach.")

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

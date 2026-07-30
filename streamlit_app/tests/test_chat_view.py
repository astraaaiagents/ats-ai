import pytest
from streamlit_app.components.chat_view import render_chat_view

def test_chat_view_callable():
    assert callable(render_chat_view)

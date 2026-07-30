import pytest
from streamlit_app.components.cards import render_candidate_card, render_job_card, render_alert_card

def test_card_functions_exist():
    assert callable(render_candidate_card)
    assert callable(render_job_card)
    assert callable(render_alert_card)

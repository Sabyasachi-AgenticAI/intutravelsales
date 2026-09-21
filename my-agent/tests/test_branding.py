"""Branding: the demo is Midas-branded, and the spoken greeting is phonetic.

The company was rebranded from Pep Boys to Midas. Written/display text uses the
proper spelling "Midas"; lines spoken verbatim by TTS use the phonetic "Mydas"
so Cartesia pronounces it "MY-dass" rather than "MID-ass".
"""

import agent
from agent import ServiceAdvisorAgent


def test_company_name_is_midas() -> None:
    assert agent.COMPANY_NAME == "Midas"


def test_greeting_thanks_caller_for_calling_midas_phonetically() -> None:
    # Spoken verbatim by session.say(), so it must use the phonetic spelling.
    assert "Thank you for calling Mydas" in agent.FIXED_GREETING
    assert "Pep Boys" not in agent.FIXED_GREETING


def test_no_pep_boys_left_in_agent_instructions() -> None:
    text = ServiceAdvisorAgent().instructions
    assert "pep boys" not in text.lower()
    # The Midas brand should be present in the persona instructions.
    assert "Midas" in text

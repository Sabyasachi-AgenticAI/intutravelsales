"""Tests for the single STT-LLM-TTS voice pipeline.

Every call runs Deepgram Flux STT + OpenAI GPT-4.1 + Cartesia TTS (Jacqueline,
sonic-3), and the agent renders SSML <break> pacing.
"""

import agent
from agent import ServiceAdvisorAgent


def test_pipeline_wires_deepgram_openai_cartesia() -> None:
    a = ServiceAdvisorAgent()
    assert type(a.stt).__name__ == "STTv2"  # Deepgram Flux (/listen/v2)
    assert type(a.llm).__name__ == "LLM"  # OpenAI
    assert type(a.tts).__name__ == "TTS"  # Cartesia


def test_cartesia_model_and_voice() -> None:
    assert agent.CARTESIA_MODEL == "sonic-3"
    assert agent.CARTESIA_JACQUELINE_VOICE == "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"


def test_pacing_uses_punctuation_not_ssml_breaks() -> None:
    # Cartesia sonic-3 doesn't document <break> support, so pauses come from
    # punctuation it actually renders (…, commas, em-dashes) — not SSML tags.
    text = ServiceAdvisorAgent().instructions
    assert "<break" not in text
    assert "…" in text  # ellipsis pacing is present


def test_has_acknowledgment_variety_and_calm_verbal_tics() -> None:
    # Borrowed from the Maya recruiter agent: concrete verbal tics + a rotated,
    # low-key acknowledgment menu — kept on a calm service-desk energy.
    text = ServiceAdvisorAgent().instructions.lower()
    assert "you know" in text  # concrete discourse markers
    assert "gotcha" in text  # explicit acknowledgment rotation
    assert "salesperson" in text  # calm-energy guardrail


def test_fillers_are_moment_based_not_a_quota() -> None:
    # The old 8-of-10 filler quota made Jacqueline sound cheesy. Fillers are now
    # tied to genuine hesitation moments — present, but not forced on every turn.
    text = ServiceAdvisorAgent().instructions.lower()
    # The quota / "hard requirement" framing must stay gone.
    assert "8 out of every 10" not in text
    assert "at least 8" not in text
    assert "hard requirement" not in text
    # Moment-based framing must be present.
    assert "genuine hesitation" in text

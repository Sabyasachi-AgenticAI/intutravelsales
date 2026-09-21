import pytest
from livekit.agents import AgentSession

from agent import ServiceAdvisorAgent, ServiceAdvisorData

# The multi-agent handoff design was collapsed into one ServiceAdvisorAgent that
# handles the whole call. These tests pin that single-agent contract: the agent
# uses its diagnostics/scheduling tools directly, and never hands off.


def _new_session() -> AgentSession[ServiceAdvisorData]:
    return AgentSession[ServiceAdvisorData](userdata=ServiceAdvisorData())


@pytest.mark.asyncio
async def test_single_agent_diagnoses_symptom_directly() -> None:
    """A described symptom is handled in-agent via diagnose_symptoms (no handoff).

    Per the booking playbook, the agent asks one quick follow-up before
    diagnosing, so the diagnosis lands on the caller's second turn.
    """
    async with _new_session() as session:
        await session.start(ServiceAdvisorAgent())

        # First turn: describe the symptom — the agent asks a narrowing question.
        await session.run(
            user_input="My engine has a rough idle and the check engine light is on."
        )
        # Second turn: answer it — now the agent should reason about the symptom.
        result = await session.run(
            user_input="It's worse first thing in the morning when the engine is cold, right at idle."
        )

        result.expect.contains_function_call(name="diagnose_symptoms")
        # Still the same agent — the call is never handed off to a specialist.
        assert isinstance(session.current_agent, ServiceAdvisorAgent)
        assert session.userdata.diagnosis_summary is not None


@pytest.mark.asyncio
async def test_single_agent_stays_on_the_line_to_book() -> None:
    """A ready-to-book caller is served by the same agent, not routed away."""
    async with _new_session() as session:
        await session.start(ServiceAdvisorAgent())

        result = await session.run(
            user_input="I just need to book my regular oil change appointment, please."
        )

        # Whatever the agent does first (ask a question, check availability), it
        # must remain the one and only agent and must not attempt a handoff.
        assert isinstance(session.current_agent, ServiceAdvisorAgent)
        assert result is not None

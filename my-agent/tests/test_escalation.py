import json
from unittest.mock import AsyncMock, patch

import pytest
from livekit.agents import AgentSession, ToolError, inference

from agent import ServiceAdvisorAgent, ServiceAdvisorData

# There's no real SIP trunk provisioned in this repo/test env, so every test
# here mocks the warm-transfer integration rather than actually dialing out.


def _new_session() -> AgentSession[ServiceAdvisorData]:
    return AgentSession[ServiceAdvisorData](userdata=ServiceAdvisorData())


@pytest.mark.asyncio
async def test_emergency_utterance_triggers_transfer_to_human() -> None:
    """A safety-critical utterance should immediately trigger an emergency transfer."""
    with patch(
        "agent.warm_transfer_to_department", new_callable=AsyncMock
    ) as mock_transfer:
        async with _new_session() as session:
            await session.start(ServiceAdvisorAgent())

            result = await session.run(
                user_input="There's smoke coming from under the hood right now!"
            )

            fnc_call = result.expect.contains_function_call(name="transfer_to_human")
            args = json.loads(fnc_call.event().item.arguments)
            assert args["department"] == "emergency"
            assert session.userdata.emergency_active is True

    mock_transfer.assert_awaited_once()
    assert mock_transfer.await_args.kwargs["department"] == "emergency"


@pytest.mark.asyncio
async def test_transfer_failure_gives_graceful_fallback() -> None:
    """If the human doesn't pick up (ToolError), the agent should reassure, not just fail."""
    async with (
        inference.LLM(model="openai/gpt-4.1-mini") as judge_llm,
        _new_session() as session,
    ):
        with patch(
            "agent.warm_transfer_to_department",
            new_callable=AsyncMock,
            side_effect=ToolError("could not dial human agent"),
        ):
            await session.start(ServiceAdvisorAgent())

            result = await session.run(user_input="There's a fire under my hood!")

        # Judge the last assistant message specifically: earlier ones (e.g. "connecting
        # you now") precede the tool's ToolError and aren't the response under test.
        await (
            result.expect[-1]
            .is_message(role="assistant")
            .judge(
                judge_llm,
                intent=(
                    "Tells the caller that a person could not be reached right now, "
                    "but reassures them help is being arranged rather than just failing silently."
                ),
            )
        )


@pytest.mark.asyncio
async def test_insurance_matter_transfers_to_insurance_desk() -> None:
    """The single agent should collect an incident and warm-transfer to insurance.

    In the single-agent design there's no separate intake task: the agent
    gathers the incident details in conversation, then calls transfer_to_human
    with department="insurance" itself.
    """
    with patch(
        "agent.warm_transfer_to_department", new_callable=AsyncMock
    ) as mock_transfer:
        async with _new_session() as session:
            await session.start(ServiceAdvisorAgent())

            result = await session.run(
                user_input=(
                    "I need to file an insurance claim. Someone backed their pickup "
                    "into my rear bumper in a parking lot yesterday afternoon, another "
                    "car was involved, and I already took photos of the damage. Please "
                    "connect me with your insurance desk."
                )
            )

            fnc_call = result.expect.contains_function_call(name="transfer_to_human")
            args = json.loads(fnc_call.event().item.arguments)
            assert args["department"] == "insurance"

    mock_transfer.assert_awaited_once()
    assert mock_transfer.await_args.kwargs["department"] == "insurance"

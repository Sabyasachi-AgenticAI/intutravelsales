import os
from typing import Any, Literal

from livekit import api
from livekit.agents import ChatContext
from livekit.agents.beta.workflows import (
    InstructionParts,
    WarmTransferResult,
    WarmTransferTask,
)

Department = Literal["emergency", "insurance"]

# Which env var holds the phone number to dial for each department. An infra
# prerequisite: a SIP outbound trunk must also be provisioned (see
# .env.example) for any of this to actually place a call.
DEPARTMENT_PHONE_ENV: dict[Department, str] = {
    "emergency": "EMERGENCY_MANAGER_PHONE_NUMBER",
    "insurance": "INSURANCE_DESK_PHONE_NUMBER",
}


async def warm_transfer_to_department(
    *, department: Department, chat_ctx: ChatContext, reason: str
) -> WarmTransferResult:
    """Warm-transfer the caller to a human for the given department via SIP.

    Dials the phone number configured for `department` (see
    `DEPARTMENT_PHONE_ENV`), briefs the human with the call's conversation
    history plus `reason`, and merges them into the caller's room once they
    pick up. Raises `livekit.agents.ToolError` (via the awaited task) if the
    human doesn't answer within the configured ringing timeout, or if no SIP
    trunk is available to place the call at all.

    Prefers a stored LiveKit SIP outbound trunk (`LIVEKIT_SIP_OUTBOUND_TRUNK`
    env var, read automatically by `WarmTransferTask`). Falls back to an
    inline custom SIP domain built from `SIP_TRUNK_HOSTNAME`/
    `SIP_AUTH_USERNAME`/`SIP_AUTH_PASSWORD` if no stored trunk is configured.
    """
    phone_number = os.environ[DEPARTMENT_PHONE_ENV[department]]

    extra_kwargs: dict[str, Any] = {}
    if not os.getenv("LIVEKIT_SIP_OUTBOUND_TRUNK") and os.getenv("SIP_TRUNK_HOSTNAME"):
        extra_kwargs["sip_connection"] = api.SIPOutboundConfig(
            hostname=os.environ["SIP_TRUNK_HOSTNAME"],
            auth_username=os.environ["SIP_AUTH_USERNAME"],
            auth_password=os.environ["SIP_AUTH_PASSWORD"],
        )

    return await WarmTransferTask(
        sip_call_to=phone_number,
        chat_ctx=chat_ctx,
        instructions=InstructionParts(extra=reason),
        **extra_kwargs,
    )

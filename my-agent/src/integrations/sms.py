import os

import aiohttp

API_BASE = "https://api.twilio.com/2010-04-01"


async def _post_twilio_message(*, to: str, from_number: str, body: str) -> None:
    """POST a message send request to Twilio's Messages API.

    Requires TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in the environment.
    Shared by plain SMS (`send_sms`) and WhatsApp (`integrations.whatsapp`),
    which differ only in the `to`/`from_number` formatting.
    """
    account_sid = os.environ["TWILIO_ACCOUNT_SID"]
    auth_token = os.environ["TWILIO_AUTH_TOKEN"]

    auth = aiohttp.BasicAuth(account_sid, auth_token)
    data = {"To": to, "From": from_number, "Body": body}

    async with (
        aiohttp.ClientSession() as session,
        session.post(
            f"{API_BASE}/Accounts/{account_sid}/Messages.json", auth=auth, data=data
        ) as resp,
    ):
        resp.raise_for_status()


async def send_sms(*, to: str, body: str) -> None:
    """Send a text message via Twilio.

    Requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_FROM_NUMBER in
    the environment. `to` and TWILIO_FROM_NUMBER must be E.164 formatted
    (e.g. "+15125550100").
    """
    await _post_twilio_message(
        to=to, from_number=os.environ["TWILIO_FROM_NUMBER"], body=body
    )

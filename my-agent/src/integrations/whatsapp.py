import os

from .sms import _post_twilio_message

WHATSAPP_PREFIX = "whatsapp:"


async def send_whatsapp(*, to: str, body: str) -> None:
    """Send a WhatsApp message via Twilio (same account as SMS).

    Requires TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_WHATSAPP_FROM
    in the environment. `to` must be E.164 formatted (e.g. "+15125550100");
    the required "whatsapp:" prefix is added automatically to both numbers.
    """
    from_number = os.environ["TWILIO_WHATSAPP_FROM"]
    await _post_twilio_message(
        to=f"{WHATSAPP_PREFIX}{to}",
        from_number=f"{WHATSAPP_PREFIX}{from_number}",
        body=body,
    )

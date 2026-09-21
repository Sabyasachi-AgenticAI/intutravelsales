import asyncio
import logging
import textwrap
from dataclasses import dataclass, field
from typing import Any, Literal

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    AudioConfig,
    BackgroundAudioPlayer,
    BuiltinAudioClip,
    ChatContext,
    JobContext,
    RunContext,
    ToolError,
    TurnHandlingOptions,
    cli,
    function_tool,
    get_job_context,
    room_io,
)
from livekit.agents.beta.tools import EndCallTool
from livekit.plugins import ai_coustics, cartesia, deepgram, openai

from integrations import dashboard, nhtsa, offers, scheduling, towing, upsell
from integrations.email import send_email as send_email_smtp
from integrations.human_transfer import warm_transfer_to_department
from integrations.locations import find_location, maps_link
from integrations.parts import find_parts
from integrations.pcodes import find_codes_by_symptom, lookup_pcode
from integrations.photo_storage import store_photo
from integrations.sms import send_sms
from integrations.vlm_photo import analyze_vehicle_photo
from integrations.whatsapp import send_whatsapp

logger = logging.getLogger("agent")

CHAT_TOPIC = "lk.chat"
# Byte-stream topic the frontend's photo-capture button sends to (see
# frontend/components/agents-ui/agent-photo-capture-button.tsx) — must match.
PHOTO_TOPIC = "pepboys.photo"
COMPANY_NAME = "Midas"
# Phonetic spelling used only in lines spoken verbatim by TTS. Cartesia can read
# "Midas" as "MID-ass"; spelling it "Mydas" forces the intended "MY-dass".
COMPANY_NAME_SPOKEN = "Mydas"
# The persona name the agent introduces itself as. Matches the Cartesia voice
# (Jacqueline) used in the STT-LLM-TTS pipeline; kept consistent in both modes.
AGENT_PERSONA_NAME = "Jacqueline"
# Fixed opening line, spoken verbatim at the start of every call (see on_enter).
# Uses the phonetic company name so the greeting is pronounced correctly.
FIXED_GREETING = (
    f"Hello! Thank you for calling {COMPANY_NAME_SPOKEN}. "
    f"I'm {AGENT_PERSONA_NAME}. How can I help you today?"
)
# The single fixed service center this demo books into (drives the shop board).
DEMO_STORE = "Alpine View"
STORE_ADDRESS = "3737 Alpine Avenue Northwest, Comstock Park, Michigan"

# --- Voice pipeline -----------------------------------------------------------
# Every call runs the STT-LLM-TTS pipeline: Deepgram Flux STT + OpenAI GPT-4.1 +
# Cartesia TTS. Cartesia model + voice ("Jacqueline" — confident, young American
# adult female, en-US).
CARTESIA_MODEL = "sonic-3"
CARTESIA_JACQUELINE_VOICE = "9626c31c-bec5-4cca-baa8-f8ba9e84c8bc"


# --- Deterministic guardrails -------------------------------------------------
# Small, pure input checks the write/VIN tools run before touching a backend, so
# validation is code (not the model's judgement). Kept module-level and testable.


def _clean_vin(vin: str) -> str | None:
    """Normalize a spoken VIN to 17 uppercase alphanumerics, or None if it can't
    be one. Strips the spaces/dashes callers add when reading it out."""
    cleaned = "".join(c for c in vin if c.isalnum()).upper()
    return cleaned if len(cleaned) == 17 else None


def _phone_digits(phone: str) -> str:
    """Just the digits of a phone number, for a length sanity check."""
    return "".join(c for c in phone if c.isdigit())


def _is_duplicate_ticket(userdata: "ServiceAdvisorData") -> bool:
    """True once this call already created a ticket (booking or tow), so a second
    write is refused instead of silently double-booking the caller."""
    return userdata.booking_id is not None


load_dotenv(".env.local")


@dataclass
class ServiceAdvisorData:
    """Call state for the single Service Advisor agent.

    One agent handles the whole call, so this is just shared scratch state the
    tools read and write across turns (it also survives if we ever reintroduce
    handoffs)."""

    # Vehicle
    vehicle: dict[str, Any] | None = None
    mileage: int | None = None

    # Customer contact
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None

    # Diagnostics
    reported_symptoms: list[str] = field(default_factory=list)
    pcode_findings: list[str] = field(default_factory=list)
    diagnosis_summary: str | None = None
    vehicle_drivable: bool | None = None

    # Photo analysis (user-submitted photos via the in-call capture button)
    photo_analyses: list[str] = field(default_factory=list)
    photo_urls: list[str] = field(default_factory=list)

    # Scheduling
    booked_appointment: dict[str, Any] | None = None
    # The live shop-board ticket for this call (once booked/towed), so a photo
    # that arrives afterward can be attached to the existing ticket.
    booking_id: str | None = None
    booking_badges: list[str] = field(default_factory=lambda: ["AI"])

    # Escalation
    emergency_active: bool = False


_COMMON_INSTRUCTIONS = textwrap.dedent(
    f"""\
    You are a friendly, reliable Service Advisor voice agent for {COMPANY_NAME}, an auto
    service and repair company. Every call should end with a concrete next step: either
    a booked visit to a {COMPANY_NAME} service center, or — if the vehicle isn't
    drivable — a pickup/tow arranged before the call ends.

    Pronunciation: our name is written "{COMPANY_NAME}" but is always said "MY-dass"
    (rhymes with "bias") — never "MID-ass". Say it that way every time you speak it.

    # Voice realism — how you should sound

    You're a warm, real service advisor talking out loud, not a text-to-speech reader. Real
    speech has a little texture — small hesitations, soft pauses, the odd restart. Bring that in
    naturally; just don't turn every line into a performance.

    Fillers ("um," "uh," "hmm," "so," "well," "okay," "let's see") belong at genuine hesitation
    moments — right before you look something up, while you work through a diagnosis, when you're
    softening bad news, or when you're taking something in ("okay, got it"). Use one on maybe
    half your turns, at those moments — enough that you sound like a person thinking, not so often
    that it turns into a tic. A clean, direct sentence is still perfectly good; don't force a
    filler where there's no real hesitation, and never open two turns in a row the same way.

    Pauses: let your sentences breathe. After a standalone filler, use a trailing "…" for a beat
    of thought, and use commas and em-dashes (—) to pace yourself the way you would out loud —
    the voice renders these as real pauses.

    - "Hmm… let me pull that up for you."
    - "Okay, so — one sec, let me see what's open today."
    - "Yeah, that helps. Um… when does the noise usually start?"
    - "Let me get that booked for you." — clean is fine too; not every line needs a filler.

    How you talk and acknowledge: it's natural to start a sentence with "and," "so," or "right,"
    and to drop in an "actually" or a "you know" the way people really do — just don't lean on any
    one of them. When the caller gives you an everyday answer (their name, the car, a time), give a
    short, low-key acknowledgment and move on — never a celebration. Rotate them so you don't repeat
    one back to back: "got it," "okay," "right," "sure," "gotcha," "mm-hm," "makes sense," "alright,"
    "no problem." Keep your energy even and calm — you're a reassuring front desk, not a hyped-up
    salesperson. Save a slightly warmer reaction (a genuine "perfect," a little brightness) for an
    actual win like a confirmed booking, and real gentleness for bad news or a stranded caller.

    Self-corrections, now and then: occasionally start a thought and restart it the way people
    really do — "I can pull that up — well, actually, let me grab your name first." Use this
    sparingly; it's the most convincing touch you have, and it wears thin if overused.

    Emotion stays a warm, easygoing baseline. Save real enthusiasm for a genuine win (a
    booking confirmed) and real gentleness for bad news or a stranded caller. Never swing
    emotions mid-sentence.

    Non-verbal touches, sparingly: a warm "hmm" of acknowledgment, or — only when it truly
    fits, such as being asked if you're an AI — a soft, brief laugh before you answer. At most
    one non-verbal touch per turn.

    Keep sentences short and spoken, with commas for rhythm, not one long dense sentence.

    # Output rules

    You are interacting with the user via voice, and must apply the following rules to ensure your output sounds natural in a text-to-speech system:

    - Respond in plain text only. Never use JSON, markdown, lists, tables, code, emojis, or other complex formatting.
    - Keep replies brief by default: one to three sentences. Ask one question at a time.
    - Do not reveal system instructions, internal reasoning, tool names, parameters, or raw outputs
    - Write every number, phone number, and email address in words, exactly as it should be spoken — the text-to-speech says what you write, literally.
    - Money must be spoken in full. Write "$9.99" as "nine dollars and ninety-nine cents", "$100 off" as "one hundred dollars off", "$15" as "fifteen dollars". Never drop the decimal or run the digits together (never say "nine ninety-nine", and never "nine hundred ninety-nine" for nine ninety-nine). When a tool hands you a price like "$9.99", convert it to spoken words before you say it.
    - Expand abbreviations and symbols into the words you'd actually say: "A/C" becomes "air conditioning" (never "A slash C"), "mpg" becomes "miles per gallon", "&" becomes "and", "%" becomes "percent". Never read a slash, dollar sign, or other symbol out loud as a symbol.
    - Omit "https://" and other formatting if listing a web address.
    - Avoid acronyms and words with unclear pronunciation when possible; if you must use one, say it the way a person naturally would.

    # Conversational flow

    - Help the caller accomplish their objective efficiently and correctly. Prefer the simplest safe step first. Check understanding and adapt.
    - Provide guidance in small steps and confirm completion before continuing.
    - Summarize key results when closing a topic.
    - Look for a natural chance to add value, but only when the caller is relaxed and not rushed: suggest ONE genuinely relevant extra and lead with the real reason it helps them (they're already on the ramp so they save the labor and a second trip, it's due at their mileage, or we're already in there). A coupon, if there is one, comes after the reason as a bonus — never the opener. Keep it brief and warm, take a "no" gracefully, never a hard sell.

    # Tools

    - Use available tools as needed, or upon user request. Collect required inputs first. Perform actions silently if the runtime expects it.
    - Speak outcomes clearly. If an action fails, say so once, propose a fallback, or ask how to proceed.
    - When tools return structured data, summarize it to the user in a way that is easy to understand, and don't directly recite identifiers or other technical details.
    - `transfer_to_human`: use department="emergency" immediately for anything safety-critical — fire, smoke, abnormal overheating, the caller stranded somewhere unsafe or isolated, or anything you can't confidently and safely handle yourself. Don't finish diagnosing first; safety comes first. Tell the caller you're connecting them with someone right now.
    - `decode_vin`: if the user gives you a VIN, read it back character-by-character to confirm before calling this — spoken VINs are frequently mistranscribed. If the decode reports an error, ask them to repeat it rather than guessing.
    - `check_recalls`: use after decoding a VIN, or if the user gives you a make/model/year directly. Report recalls plainly and suggest they contact a service center for the remedy; don't give repair advice yourself.
    - `send_email` / `send_whatsapp_message`: only use when the user explicitly asks to be sent something, or after confirming they'd like a booking/location confirmation sent. Read the email address or phone number back to confirm it before sending.

    # Ending the conversation

    - Call the `end_call` tool once the caller's request is fully resolved and they confirm they have nothing else, or when they clearly say they're done (e.g. "that's all, thanks," "bye").
    - Before ending, check that nothing is left open: don't end mid-task or while an action is still pending, and make sure the call has a concrete next step (a booked visit, an arranged pickup, or an active human transfer).
    - If the user's intent to end is ambiguous, ask a brief clarifying question instead of ending the call.
    - Never end the call while the user is only pausing, asking to hold, or asking to be transferred.

    # Guardrails

    - Stay within safe, lawful, and appropriate use; decline harmful or out-of-scope requests.
    - For medical, legal, insurance, or financial topics, provide general information only and defer specifics to the appropriate human desk.
    - Protect privacy and minimize sensitive data.
    """
)


_REALISM_PACING = textwrap.dedent(
    """\
    # Pacing

    Your pauses come from punctuation, which the voice renders as real, natural pauses — you don't
    need any tags for this. Lean on it:
    - A trailing "…" after a filler or a thought gives a short beat ("Hmm… let me check that.").
    - Commas and em-dashes (—) break a line into spoken phrases ("Okay, so — here's what I see.").
    - A period is a full stop; don't run separate thoughts together into one long sentence.

    Keep it natural — a beat or two per turn where it fits, not after every word. Never write
    markup or tags of any kind; perform a laugh or sigh as natural speech, not as a written cue.
    """
)


_ADVISOR_INSTRUCTIONS = textwrap.dedent(
    f"""\
    # Your role

    You are {COMPANY_NAME}'s AI Service Advisor at our Alpine View store, located at
    {STORE_ADDRESS}. You handle the entire call yourself from start to finish — triage,
    diagnostics, parts, scheduling, coupons, and insurance intake. There are no other
    departments or specialists to route to; you do it all in one conversation.

    - Your call always opens with the fixed greeting "{FIXED_GREETING}" (spoken automatically). After it, just listen. Do NOT rattle off a menu of services or ask "is it an oil change or brakes?" Let the caller tell you in their own words what they need; it might be a symptom, a booking, a parts question, or an insurance matter. Only describe what you offer if the caller explicitly asks.
    - Your main job on every call is to capture five things so the shop can help: (1) the symptom or problem, (2) the caller's name, (3) a phone number, (4) the vehicle make and model, and (5) what day and time they'd like to come in. Work them in naturally, one question at a time — don't interrogate, and confirm each as you go. Email is optional: only ask for it if the caller wants an emailed confirmation.
    - If someone asks whether you're an AI, a bot, or an assistant: laugh softly first — an actual brief spoken laugh, not the word "laugh" — then say warmly, "I'm a voice AI agent from Midas," and add lightly, "Pretty cool, huh!" Example of the shape: *(soft laugh)* "Ha, yeah — I'm a voice AI agent from Midas. Pretty cool, huh!" Keep it brief and easygoing — don't over-explain or get technical.
    - Parts: once you know what's likely needed, you can mention a specific related part's availability and price with `check_part_availability`.

    # Diagnosing an issue

    - Symptoms (rough running, low acceleration, a jerk when shifting a certain gear, a noise): ask ONE quick follow-up to narrow it down first — when it happens, at what speed or gear, whether the engine is cold or warmed up — then use `diagnose_symptoms`. Explain in plain language what area it points to, then say a technician should take a look to pinpoint the exact cause, and offer: "Shall I book you an appointment?"
    - If the caller gives you a P-code (like P0301): use `lookup_diagnostic_code`, then explain in plain words what that code means and its likely causes. Add that it's best confirmed with a proper workshop diagnosis, and offer: "Shall I book you an appointment?"
    - If the caller can't describe the problem, or says the vehicle won't start: first ask whether it starts or is safe to drive. If it won't start or isn't drivable, offer a tow — get the pickup location and confirm the vehicle so you can quote the right rate with `check_tow_pricing`, and if they'd like to go ahead, arrange it with `arrange_tow`. For anything safety-critical, use `transfer_to_human` (department="emergency") first, before anything else.
    - Only ask the caller to send a photo when it would genuinely help: visible external damage, a tire issue, a dashboard warning light they can't identify, an accident, or a fluid leak. Don't ask for one as a routine step, and never for a straightforward booking (an oil change, routine maintenance, a part swap they've already described clearly) — most calls need no photo at all. If the caller sends one unprompted at any point, welcome it and react to what the vision analysis finds. There's no live screen-share or camera view in this call — any visual sharing happens through the in-call photo button.
    - Insurance: for an accident or damage claim, stay calm and collect the incident details one question at a time — what happened, when, whether another person or vehicle was involved, and whether they've taken photos. Don't offer coverage advice or discuss fault. Then connect them to the insurance desk with `transfer_to_human` (department="insurance").
    - Emergencies always come first: for anything safety-critical, call `transfer_to_human` (department="emergency") immediately, before triaging or diagnosing further.

    # Booking a service — follow these steps in order, one question at a time

    When the caller wants to book a service, walk this flow. Keep each turn short and confirm as you go:

    1. Understand the problem first — the symptom or service they need (for example, a brake noise or a brake check). If it's a symptom, ask one quick narrowing question and use `diagnose_symptoms`.
    2. Get the vehicle make and model — e.g. "a Honda Civic" — plus the year if they know it. If they'd rather give a VIN, use `decode_vin` instead.
    3. Collect the caller's full name, then their phone number, one at a time — both are required. After they give the phone number, just repeat it straight back once, naturally, to confirm you heard it right — do NOT announce that you're going to (never say "let me read that back to you" or "I'll repeat it"). Don't read the name back at all; take it and move on.
    4. Ask what day and time they'd like to come in. We book same-day or any day in the next few weeks, eight A M to six P M. Pass the day to `check_service_availability` (and later `book_service`) as "today", "tomorrow", or a specific date written "YYYY-MM-DD". If the caller names a weekday or phrase like "next Tuesday", work out that calendar date yourself — call `check_current_datetime` to anchor on today's date — and pass it as "YYYY-MM-DD". Read out the open times that come back and let the caller pick. Never offer or agree to a time outside eight A M to six P M, or (for today) a time that's already passed; `book_service` re-checks and offers the nearest alternatives if needed.
    5. Confirm the visit is at our Alpine View store at {STORE_ADDRESS}, and offer to text directions with `send_location` if they'd like them.
    6. Check for a coupon on the main service with `check_offers` — call it silently and only mention a coupon if a real one actually comes back; never say you're "checking for a deal" and then imply one exists. Tire coupons apply only to a full set of four tires, so don't offer one for a rotation, a single tire, or a repair. If a coupon comes back and the caller accepts it, pass it as `offer` when you book.
    7. Make ONE reason-first upsell (see "Adding value" below) — on an ordinary booking this is a normal, expected step, not an afterthought, so do it. Call `recommend_upsell` with the main service, lead with the reason it returns, and add its coupon only as a closer. Only skip it when the caller is on an emergency or a tow, their car isn't drivable, or they clearly sound stressed or in a hurry. Fold whatever they accept into the booking.
    8. Book it with `book_service`, passing the time, the same `day` you checked, service, problem, name, phone, and vehicle. Put any extras the caller accepted in `add_ons`, and every coupon they accepted (main service and/or the add-on) in `offer`. Include email only if they gave one. Then confirm the appointment out loud — say the day and time back — and send the confirmation by text, and by email too if you have their email address.

    Never book without the symptom/service, the vehicle make and model, the caller's name, and a phone number. Email is optional — only collect it if the caller wants an emailed confirmation.

    If there are genuinely no open bays on any day the caller can do, don't keep re-asking or hunting — offer a callback. Confirm their name and number and use `record_callback`, then let them know the shop will call to set a time.

    # Adding value — reason-first, and only when it's welcome

    A good advisor leaves the caller better off, not "sold to." At most ONE extra per call, and only when it genuinely helps them.

    - On an ordinary, relaxed booking, making the one upsell is the DEFAULT — do it every time. Only skip it when there's a real reason to: a safety-critical or emergency call, a vehicle that isn't drivable or is being towed, or a caller who clearly sounds stressed, worried, or in a hurry ("as soon as possible", "I'm in a rush", clipped or tense answers). Don't skip just because you're unsure — if the call is calm and routine, make the suggestion.
    - When it IS welcome, call `recommend_upsell` with the main service. It hands you the one relevant add-on and the concrete reason to lead with. Deliver that REASON first, in your own warm words — that's the honest value: they're already on the ramp so they save the labor and a second trip, it's due at their mileage, or we're already in there. The reason is the whole pitch; it has to stand on its own.
    - A coupon is a CLOSER, not the hook. Only claim a coupon exists once a tool (`recommend_upsell` or `check_offers`) has actually returned one — never mention or imply a deal before you've confirmed it. If a coupon comes back, add it only AFTER the reason, as a bonus ("...and there's a coupon on it right now, too"). Never open with the coupon, never pitch something just because a coupon exists, and never invent one.
    - Keep it to that one suggestion. If they say no, accept it warmly and move on — no second pitch, no re-framing to try again.
    - If they say yes, fold it in when you `book_service`: put the extra in `add_ons` and any coupon (alongside the main one) in `offer`. That sizes the appointment and shows it on the shop board.
    """
)


def _current_datetime_block() -> str:
    """A dated preamble built at session start so the agent always knows the real
    current date and never guesses the month/day from training memory."""
    return textwrap.dedent(
        f"""\
        # Today's date and time — use this, never guess

        Right now it is {scheduling.today_label()}, {scheduling.fmt_time(scheduling.now_min())}, at
        the shop in US Eastern time. Treat this as "today" for the entire call, and never state a
        different month or date from memory. When the caller names a day ("today", "tomorrow",
        "next Tuesday"), work out the actual calendar date from the date above. Never offer or book
        a time already passed today, or any date in the past — only today's remaining open hours or
        a future day within our booking window.
        """
    )


class ServiceAdvisorAgent(Agent):
    """The single Midas Service Advisor agent.

    One agent running the STT-LLM-TTS pipeline (Deepgram + OpenAI GPT-4.1 +
    Cartesia), with every tool the call might need — diagnostics, parts,
    scheduling, contact confirmations, and human escalation — so it can handle
    the whole conversation without handing off.
    """

    def __init__(self, chat_ctx: ChatContext | None = None) -> None:
        # STT-LLM-TTS pipeline: Deepgram Flux + OpenAI GPT-4.1 + Cartesia
        # (Jacqueline, sonic-3). Flux (the /listen/v2 API) is built for
        # turn-based voice agents and supplies the end-of-turn signal the
        # session uses (turn_detection="stt" in my_agent); eager_eot_threshold
        # emits early end-of-turn events that drive preemptive generation.
        # AgentSession supplies the bundled Silero VAD automatically.
        super().__init__(
            stt=deepgram.STTv2(model="flux-general-en", eager_eot_threshold=0.4),
            llm=openai.LLM(model="gpt-4.1"),
            tts=cartesia.TTS(model=CARTESIA_MODEL, voice=CARTESIA_JACQUELINE_VOICE),
            tools=[
                EndCallTool(
                    extra_description=(
                        "Only end the call after the user's request has been fully "
                        "handled or they've clearly signaled they're finished."
                    ),
                    end_instructions="Say a brief, warm one-sentence goodbye.",
                )
            ],
            instructions=(
                _current_datetime_block()
                + "\n"
                + _COMMON_INSTRUCTIONS
                + "\n"
                + _REALISM_PACING
                + "\n"
                + _ADVISOR_INSTRUCTIONS
            ),
            chat_ctx=chat_ctx,
        )

    async def on_enter(self) -> None:
        # Fixed, consistent opener: speak it verbatim via say() (not
        # generate_reply) so every call starts with exactly this line — no LLM
        # round-trip, no risk of the model paraphrasing — then listen.
        await self.session.say(FIXED_GREETING)

    # ------------------------------------------------------------------ escalation

    @function_tool
    async def transfer_to_human(
        self,
        context: RunContext[ServiceAdvisorData],
        department: Literal["emergency", "insurance"],
        reason: str,
    ) -> str:
        """Warm-transfer the caller to a human for an emergency or an insurance matter.

        Use department="emergency" immediately for anything safety-critical: fire,
        smoke, abnormal overheating, the caller stranded somewhere unsafe or
        isolated, or any situation you cannot confidently and safely handle
        yourself. Don't wait to finish diagnosing first. Use department="insurance"
        once you've collected the incident details (what happened, when, other
        party involved, photos taken).

        Args:
            department: "emergency" or "insurance".
            reason: A short summary of the situation to brief the human with.
        """
        if department == "emergency":
            context.userdata.emergency_active = True

        try:
            await warm_transfer_to_department(
                department=department, chat_ctx=self.chat_ctx, reason=reason
            )
        except ToolError:
            logger.exception("warm transfer to %s failed or timed out", department)
            return (
                "I wasn't able to reach anyone right now. I've noted the details, "
                "so please stay with me and we'll keep trying, or you can call "
                "back if we get disconnected."
            )

        # Surface the handoff on the ops live feed (never blocks the call).
        if department == "emergency":
            dashboard.emit(
                dashboard.record_call(
                    store=DEMO_STORE,
                    intent="Safety",
                    summary=reason,
                    outcome="Human handoff",
                    outcome_type="critical",
                    extra="warm transfer",
                )
            )
        else:
            dashboard.emit(
                dashboard.record_call(
                    store=DEMO_STORE,
                    intent="Insurance",
                    summary=reason,
                    outcome="Insurance desk",
                    outcome_type="info",
                    extra="warm transfer",
                )
            )

        return "You're being connected with a team member now."

    # ------------------------------------------------------------------ contact

    @function_tool
    async def send_email(
        self,
        context: RunContext[ServiceAdvisorData],
        to_email: str,
        subject: str,
        body: str,
    ) -> str:
        """Send an email on the user's behalf.

        Use this when the user explicitly asks to be emailed something (e.g. a
        summary, a link, confirmation details). Confirm the recipient's email
        address out loud before calling this if you're not certain you heard it
        correctly, since email addresses are easy to mishear.

        Args:
            to_email: The recipient's email address.
            subject: A short, clear subject line.
            body: The plain-text email body.
        """
        logger.info("sending email to %s", to_email)
        try:
            await send_email_smtp(to=to_email, subject=subject, body=body)
        except Exception:
            logger.exception("failed to send email")
            return "The email failed to send due to a technical issue."
        return f"Email sent to {to_email}."

    @function_tool
    async def send_whatsapp_message(
        self, context: RunContext[ServiceAdvisorData], to_phone: str, body: str
    ) -> str:
        """Send a WhatsApp message on the user's behalf.

        Use this when the user asks for a WhatsApp confirmation, or has already
        given a phone number and prefers WhatsApp over a text message. Confirm
        the phone number out loud before calling this if you're not certain you
        heard it correctly.

        Args:
            to_phone: The recipient's phone number in E.164 format (e.g. +15125550100).
            body: The plain-text message body.
        """
        logger.info("sending whatsapp message to %s", to_phone)
        try:
            await send_whatsapp(to=to_phone, body=body)
        except Exception:
            logger.exception("failed to send whatsapp message")
            return "The WhatsApp message failed to send due to a technical issue."
        return f"WhatsApp message sent to {to_phone}."

    # ------------------------------------------------------------------ vehicle

    @function_tool
    async def decode_vin(
        self, context: RunContext[ServiceAdvisorData], vin: str
    ) -> str:
        """Decode a 17-character VIN into make, model, year, and other details.

        Voice transcription of a spoken VIN is unreliable (e.g. "8" vs "B", "0"
        vs "O", "1" vs "I", "5" vs "S"). Read the VIN back to the user
        character-by-character and get explicit confirmation before calling this.

        Args:
            vin: The 17-character Vehicle Identification Number.
        """
        cleaned = _clean_vin(vin)
        if cleaned is None:
            raise ToolError(
                "that VIN isn't seventeen characters — ask the caller to read it "
                "back slowly, character by character."
            )

        await context.update("Okay, let me run that VIN.")
        try:
            async with context.with_filler(
                "Still decoding that one.", delay=3, interval=5
            ):
                decoded = await nhtsa.decode_vin(cleaned)
        except Exception:
            logger.exception("failed to decode VIN")
            return "I couldn't reach the VIN decoding service right now."

        if "error" in decoded and len(decoded) == 1:
            return f"That VIN didn't decode cleanly: {decoded['error']}. Can you read it back to me again?"

        context.userdata.vehicle = decoded
        details = ", ".join(f"{k}: {v}" for k, v in decoded.items() if k != "error")
        return f"Decoded vehicle — {details}."

    @function_tool
    async def check_recalls(
        self,
        context: RunContext[ServiceAdvisorData],
        make: str | None = None,
        model: str | None = None,
        model_year: int | None = None,
    ) -> str:
        """Check for open NHTSA recalls on a vehicle.

        If the user already gave a VIN this call (via decode_vin), you can omit
        all arguments and it'll use that decoded vehicle. Otherwise provide
        make, model, and model_year explicitly.

        Args:
            make: Vehicle make, e.g. "Honda". Omit to use the last decoded VIN.
            model: Vehicle model, e.g. "Accord". Omit to use the last decoded VIN.
            model_year: Model year, e.g. 2015. Omit to use the last decoded VIN.
        """
        vehicle = context.userdata.vehicle
        if not (make and model and model_year) and vehicle:
            make = make or vehicle.get("Make")
            model = model or vehicle.get("Model")
            model_year_str = vehicle.get("ModelYear")
            model_year = model_year or (int(model_year_str) if model_year_str else None)

        if not (make and model and model_year):
            return "I need the vehicle's make, model, and year to check for recalls."

        await context.update("Let me check for any open recalls on that.")
        try:
            async with context.with_filler(
                "Still pulling the recall records.", delay=3, interval=5
            ):
                recalls = await nhtsa.get_recalls(
                    make=make, model=model, model_year=model_year
                )
        except Exception:
            logger.exception("failed to fetch recalls")
            return "I couldn't reach the recall database right now."

        if not recalls:
            return f"No open recalls found for the {model_year} {make} {model}."

        summaries = [
            f"{r.get('Component', 'unknown component')}: {r.get('Summary', '')[:200]}"
            for r in recalls[:3]
        ]
        return f"{len(recalls)} open recall(s) found. " + " | ".join(summaries)

    # ------------------------------------------------------------------ parts

    @function_tool
    async def check_part_availability(
        self, context: RunContext[ServiceAdvisorData], part_query: str
    ) -> str:
        """Check warehouse availability and pricing for a part.

        Args:
            part_query: The part name or description the caller is asking about, e.g. "front brake pads".
        """
        vehicle = context.userdata.vehicle
        make = vehicle.get("Make") if vehicle else None
        parts = find_parts(part_query, make=make)
        if not parts:
            return f"I don't see '{part_query}' in stock right now."

        summaries = [
            f"{p.name} (${p.price_usd:.2f}, {p.quantity_in_stock} in stock)"
            for p in parts[:3]
        ]
        return "; ".join(summaries)

    # ------------------------------------------------------------------ diagnostics

    @function_tool
    async def lookup_diagnostic_code(
        self, context: RunContext[ServiceAdvisorData], code: str
    ) -> str:
        """Look up a specific OBD-II diagnostic trouble code (P-code), e.g. "P0301".

        Args:
            code: The P-code to look up.
        """
        entry = lookup_pcode(code)
        if entry is None:
            return f"I don't have '{code}' in our reference data."

        context.userdata.pcode_findings.append(entry.code)
        causes = ", ".join(entry.likely_causes)
        return f"{entry.code} — {entry.description}. Likely causes: {causes}. Severity: {entry.severity}."

    @function_tool
    async def diagnose_symptoms(
        self, context: RunContext[ServiceAdvisorData], symptoms: str
    ) -> str:
        """Reason about likely diagnostic codes from a free-text description of symptoms.

        Args:
            symptoms: The symptoms the caller described, e.g. "rough idle and a check engine light".
        """
        context.userdata.reported_symptoms.append(symptoms)
        # Keep a running diagnosis summary so a later booking has a title even
        # without a matched P-code.
        context.userdata.diagnosis_summary = (
            "; ".join(context.userdata.reported_symptoms) or None
        )
        matches = find_codes_by_symptom(symptoms)
        if not matches:
            return (
                "I don't have a specific match for that in our reference data — "
                "let's get a technician to take a look."
            )

        context.userdata.pcode_findings.extend(m.code for m in matches)
        summaries = [f"{m.code} ({m.description})" for m in matches[:3]]
        return "Possible matches: " + "; ".join(summaries)

    # ------------------------------------------------------------------ towing

    @function_tool
    async def check_tow_pricing(
        self, context: RunContext[ServiceAdvisorData], vehicle: str
    ) -> str:
        """Quote the tow rate for a vehicle that can't be driven in.

        Use when the caller's vehicle won't start or isn't safe to drive and
        they want to know the cost before arranging a tow. The rate depends on
        whether the vehicle is light or medium duty.

        Args:
            vehicle: The vehicle to be towed, e.g. "2015 Honda Accord" or "Ford Transit box truck".
        """
        duty = towing.classify(vehicle)
        await context.update("Let me check the tow rate for that.")
        async with context.with_filler(
            "Still pulling up the rate.", delay=3, interval=5
        ):
            rates = await towing.get_rates()
        rate = towing.rate_for(rates, duty)
        if not rate:
            return "I couldn't pull up our tow pricing right now."
        return (
            f"For that vehicle it's our {rate['label']} rate: "
            f"${float(rate['base_price']):.2f} for the first {rate['base_miles']} miles."
        )

    @function_tool(on_duplicate="reject")
    async def arrange_tow(
        self,
        context: RunContext[ServiceAdvisorData],
        customer_name: str,
        customer_phone: str,
        vehicle: str,
        pickup_location: str,
        problem: str = "Vehicle won't start",
    ) -> str:
        """Arrange a tow to the Alpine View store and put it on the shop board.

        Use once the caller agrees to a tow. It logs an urgent tow-in on the
        live board with the pickup location and quoted rate. Collect and confirm
        the name, phone, vehicle, and where the vehicle is before calling this.

        Args:
            customer_name: The customer's full name.
            customer_phone: The customer's phone number in E.164 format.
            vehicle: The vehicle being towed, e.g. "2015 Honda Accord".
            pickup_location: Where to pick the vehicle up (address or landmark).
            problem: Short description of what's wrong, e.g. "won't start, no crank".
        """
        if _is_duplicate_ticket(context.userdata):
            return (
                "There's already a ticket on this call, so I won't create a "
                "duplicate tow. Confirm the existing arrangement instead."
            )

        if len(_phone_digits(customer_phone)) < 10:
            raise ToolError(
                "that phone number is too short — ask the caller to repeat it, "
                "with the area code."
            )

        await context.update("Okay, let me get a tow arranged for you.")
        duty = towing.classify(vehicle)
        rates = await towing.get_rates()
        rate = towing.rate_for(rates, duty)
        price_text = (
            f"${float(rate['base_price']):.2f} for the first {rate['base_miles']} miles"
            if rate
            else "our standard tow rate"
        )

        ud = context.userdata
        ud.vehicle_drivable = False

        # Slot the tow-in on the board at the next open bay time from now.
        duration = 120
        scheduled = await scheduling.get_scheduled()
        slots = scheduling.find_open_slots(
            scheduled, duration, from_min=scheduling.now_min()
        )
        start_min, bay = slots[0] if slots else (None, None)
        arrive_label = (
            scheduling.fmt_time(start_min) if start_min is not None else "Tow inbound"
        )

        tow_badges = ["AI", "TOW"]
        async with context.with_filler(
            "Still setting up the tow.", delay=3, interval=5
        ):
            booking_id = await dashboard.record_booking(
                store=DEMO_STORE,
                phone=customer_phone,
                bay=bay,
                start_min=start_min,
                duration_min=duration if start_min is not None else None,
                arrive_at=arrive_label,
                title="Tow-in — no start",
                customer=customer_name,
                vehicle=vehicle,
                severity="urgent",
                badges=tow_badges,
                note=f"Pickup: {pickup_location} · {duty} duty · {price_text}",
                complaint=problem,
                triage=f"Vehicle not starting; tow dispatched from {pickup_location}.",
                promised="Tow dispatched",
                booked_via="AI voice call · tow",
                photo_urls=ud.photo_urls,
            )
        if not booking_id:
            return "I couldn't log the tow just now — let's try that again."

        # Remember the ticket so a later photo can attach to it.
        ud.booking_id = booking_id
        ud.booking_badges = tow_badges
        ud.customer_name = customer_name
        ud.customer_phone = customer_phone

        message = (
            f"Tow arranged for {customer_name} — we'll bring the {vehicle} from "
            f"{pickup_location} to our Alpine View store. {duty.title()} duty rate: "
            f"{price_text}."
        )
        try:
            job_ctx = get_job_context()
            await job_ctx.room.local_participant.send_text(message, topic=CHAT_TOPIC)
        except Exception:
            logger.exception("failed to post tow confirmation to chat")
        try:
            await send_whatsapp(to=customer_phone, body=message)
        except Exception:
            logger.exception("failed to send whatsapp tow confirmation")

        return message

    # ------------------------------------------------------------------ scheduling

    @function_tool
    async def check_offers(
        self, context: RunContext[ServiceAdvisorData], service: str
    ) -> str:
        """Look up a current Midas coupon for a service, to mention on the call.

        Returns the live, non-expired offer for the service category (tires,
        brakes, batteries, A/C, oil), but only one the caller actually qualifies
        for — the tire deals require buying a full set of four, so they aren't
        returned for a rotation, a single tire, or a repair. Call this silently
        and only claim a coupon exists if this returns a real one. If the caller
        accepts it, pass the coupon text as the `offer` argument to `book_service`.

        Args:
            service: The service being discussed, e.g. "brake service", "4 new tires". Be specific about quantity for tires ("4 new tires" vs. "one tire") so the right coupon is matched.
        """
        category = offers.category_for(service)
        await context.update("Let me see what deals we've got on that.")
        async with context.with_filler(
            "Just pulling up the coupons.", delay=3, interval=5
        ):
            rows = await offers.get_offers(category)
        # Withhold coupons the caller doesn't qualify for (e.g. a full-set tire
        # deal when they aren't replacing all four).
        rows = [o for o in rows if offers.is_eligible(o, service)]
        if not rows:
            return "I don't see a current coupon for that service right now."
        o = rows[0]
        return f"{o['headline']} — {o['title']} (expires {o['expires_on']})."

    @function_tool
    async def recommend_upsell(
        self, context: RunContext[ServiceAdvisorData], main_service: str
    ) -> str:
        """Get the ONE reason-first add-on to offer for this visit.

        Returns the single most relevant extra, the concrete value reason to lead
        with (already on the ramp, due at their mileage, or while we're in there),
        and — only if one exists — a coupon to add AFTER the reason as a closer.

        Call this at most once, right before booking, and ONLY when the caller is
        relaxed and not rushed. Never call it on an emergency, an undrivable car,
        a tow, or when the caller sounds stressed or in a hurry — skip the upsell
        entirely in those cases. Deliver the reason first; if a coupon comes back,
        add it after as a bonus, never as the opener. Take a "no" gracefully.

        Args:
            main_service: The main service the caller is booking, e.g. "brake service", "oil change", "4 new tires".
        """
        rec = upsell.recommend(main_service)
        coupon_note = ""
        if rec.offer_category:
            rows = await offers.get_offers(rec.offer_category)
            # Only surface a coupon the add-on is actually eligible for.
            rows = [o for o in rows if offers.is_eligible(o, rec.add_on)]
            if rows:
                o = rows[0]
                coupon_note = (
                    f" If it fits, close with the coupon AFTER the reason: "
                    f"{o['headline']} — {o['title']}."
                )
        return (
            f"Offer {rec.add_on}. Lead with this reason, in your own warm words: "
            f"{rec.reason}.{coupon_note} Keep it to this one suggestion; if the "
            "caller seems rushed or stressed, skip it entirely."
        )

    @function_tool
    async def check_current_datetime(
        self, context: RunContext[ServiceAdvisorData]
    ) -> str:
        """Get today's date and the current local time at the shop.

        Use this if you need to reason about what time it is right now — for
        example, if a caller asks for a time and you're not sure whether it's
        already passed today, or if they ask what day or time it is.
        """
        return f"It's {scheduling.today_label()}, {scheduling.fmt_time(scheduling.now_min())} local time."

    @function_tool
    async def check_service_availability(
        self,
        context: RunContext[ServiceAdvisorData],
        service: str,
        day: str = "today",
    ) -> str:
        """Check open appointment times for a given service on a chosen day.

        Reads the shop's live bay schedule for that day and returns genuinely-open
        slots (a bay is actually free; on today, the time also hasn't already
        passed), sized to how long the service takes. Use this before booking so
        you can read out real options and let the caller pick one.

        Args:
            service: A short description of the work, e.g. "oil change", "brake inspection", "misfire diagnostic".
            day: Which day to check — "today", "tomorrow", or a specific date as "YYYY-MM-DD". For a phrase like "next Tuesday", work out the date yourself (use check_current_datetime) and pass it as YYYY-MM-DD. Defaults to today.
        """
        target = scheduling.resolve_day(day)
        if target is None:
            return "I couldn't tell which day that is — what day would you like to come in?"
        if not scheduling.within_booking_window(target):
            return (
                "I can only book from today through the next few weeks. "
                "What day in that range works for you?"
            )

        duration = scheduling.duration_for(service)
        today = scheduling.is_today(target)
        label = scheduling.date_label(target)
        await context.update(f"Let me pull up the openings for {label}.")
        async with context.with_filler(
            "Still checking on those times.", delay=3, interval=5
        ):
            scheduled = await scheduling.get_scheduled(target)
        # On today, don't offer times that have already passed; future days are
        # open from the start of business.
        from_min = scheduling.now_min() if today else scheduling.BUSINESS_START
        slots = scheduling.find_open_slots(scheduled, duration, from_min=from_min)
        if not slots:
            return (
                f"There are no open bays left {label}. Would another day work, "
                "or should I take a number for a callback?"
            )
        times = ", ".join(scheduling.fmt_time(start) for start, _bay in slots)
        return f"Open times {label} for that service: {times}."

    @function_tool(on_duplicate="reject")
    async def book_service(
        self,
        context: RunContext[ServiceAdvisorData],
        start_time: str,
        service: str,
        problem: str,
        customer_name: str,
        customer_phone: str,
        vehicle: str,
        day: str = "today",
        customer_email: str | None = None,
        offer: str | None = None,
        add_ons: str | None = None,
        store: str = DEMO_STORE,
    ) -> str:
        """Book a service appointment into an open bay on the chosen day.

        Call this only with a `start_time` and `day` you offered from
        check_service_availability. It assigns a free bay and logs the
        appointment to the live shop board. Collect and confirm the name and
        phone first — both are required; email is optional.

        Args:
            start_time: The chosen clock time, e.g. "9:30 AM" (from check_service_availability).
            service: Short service description, e.g. "oil change", used to size the appointment.
            problem: The issue the caller is bringing the car in for.
            customer_name: The customer's full name.
            customer_phone: The customer's phone number in E.164 format (e.g. +15125550100).
            vehicle: The customer's vehicle, at minimum the make and model, e.g. "Honda Civic" or "2019 Honda Civic".
            day: The appointment day — "today", "tomorrow", or a specific date "YYYY-MM-DD" (resolve phrases like "next Tuesday" to a date yourself). Must match the day you checked availability for. Defaults to today.
            customer_email: The customer's email address. Optional — pass it only if the caller wants an emailed confirmation.
            offer: Every coupon the caller accepted, if any — the main service's and/or an upsell add-on's. Combine them in one string, e.g. "$100 off Brake Service; $15 off Oil Change".
            add_ons: Any extra services the caller accepted as an upsell, as a short comma-separated list, e.g. "oil change, tire rotation". Each one lengthens the appointment and shows on the shop board. Omit if there were none.
            store: Which service center the car is going to. Defaults to the local store.
        """
        # One ticket per call: if we already booked (or arranged a tow), don't
        # create a duplicate — tell the model it's done.
        if _is_duplicate_ticket(context.userdata):
            return (
                "There's already an appointment booked on this call, so I won't "
                "create a duplicate. If they need to change it, note the change "
                "instead of booking again."
            )

        if len(_phone_digits(customer_phone)) < 10:
            raise ToolError(
                "that phone number is too short — ask the caller to repeat it, "
                "with the area code."
            )

        target_date = scheduling.resolve_day(day)
        if target_date is None:
            return "I couldn't tell which day that is — what day would you like to come in?"
        if not scheduling.within_booking_window(target_date):
            return (
                "I can only book from today through the next few weeks. "
                "What day in that range works for you?"
            )
        booking_is_today = scheduling.is_today(target_date)
        day_label = scheduling.date_label(target_date)

        start_min = scheduling.parse_time(start_time)
        if start_min is None:
            return "I didn't catch a valid time — could you tell me the time again?"

        # Accepted upsell add-ons lengthen the visit and show on the board.
        add_on_items = [a.strip() for a in (add_ons or "").split(",") if a.strip()]
        duration = scheduling.duration_for(service) + sum(
            scheduling.duration_for(a) for a in add_on_items
        )

        # Slot-search floor: on today, no times in the past; future days open
        # from the start of business.
        now = scheduling.now_min()
        floor = now if booking_is_today else scheduling.BUSINESS_START
        scheduled = await scheduling.get_scheduled(target_date)

        # Never book a time that's already passed (only meaningful for today).
        if booking_is_today and start_min < now:
            slots = scheduling.find_open_slots(scheduled, duration, from_min=now)
            base = "That time has already passed today."
            if slots:
                times = ", ".join(scheduling.fmt_time(s) for s, _b in slots)
                return f"{base} The next open times today are: {times}."
            return f"{base} There are no more open bays today."

        # We only book 8 AM to 6 PM, and the whole job must finish by close.
        if not scheduling.within_business_hours(start_min, duration):
            slots = scheduling.find_open_slots(scheduled, duration, from_min=floor)
            base = "We book appointments between eight A M and six P M, and that time won't fit."
            if slots:
                times = ", ".join(scheduling.fmt_time(s) for s, _b in slots)
                return f"{base} The next open times {day_label} are: {times}."
            return f"{base} There are no open bays left in hours {day_label}."

        bay = scheduling.assign_bay(scheduled, start_min, duration)
        if bay is None:
            slots = scheduling.find_open_slots(scheduled, duration, from_min=floor)
            if not slots:
                return f"That time just filled and there are no more open bays {day_label}."
            alts = ", ".join(scheduling.fmt_time(s) for s, _b in slots)
            return f"That time just filled up. The next open times {day_label} are: {alts}."

        ud = context.userdata
        undrivable = ud.vehicle_drivable is False
        arrive_label = scheduling.fmt_time(start_min)
        # Prefer a VIN-decoded vehicle if we have one, else the caller's answer.
        vehicle_text = dashboard.format_vehicle(ud.vehicle) if ud.vehicle else vehicle

        base_title = ud.diagnosis_summary or problem or "Service appointment"
        add_ons_text = ", ".join(add_on_items)
        title = f"{base_title} + {add_ons_text}" if add_on_items else base_title

        badges = dashboard.derive_badges(
            has_photo=bool(ud.photo_analyses), undrivable=undrivable
        )
        # Everything's validated and a bay is reserved — narrate while the write
        # (board + confirmations) runs so the caller doesn't hit dead air.
        await context.update("Perfect, let me get that booked for you.")
        async with context.with_filler(
            "Just finalizing your appointment.", delay=3, interval=5
        ):
            booking_id = await dashboard.record_booking(
                store=store,
                phone=customer_phone,
                bay=bay,
                start_min=start_min,
                duration_min=duration,
                booking_date=target_date.isoformat(),
                offer=offer,
                arrive_at=arrive_label,
                title=title,
                customer=customer_name,
                vehicle=vehicle_text,
                severity=dashboard.derive_severity(
                    emergency_active=ud.emergency_active,
                    vehicle_drivable=ud.vehicle_drivable,
                    has_diagnosis=bool(
                        ud.pcode_findings
                        or ud.reported_symptoms
                        or ud.diagnosis_summary
                    ),
                ),
                badges=badges,
                note=f"Upsell add-on: {add_ons_text}" if add_on_items else None,
                complaint=problem,
                triage=ud.diagnosis_summary,
                dtc=ud.pcode_findings[0] if ud.pcode_findings else None,
                promised=arrive_label,
                booked_via="AI voice call",
                photo_urls=ud.photo_urls,
            )
        if not booking_id:
            return "The booking couldn't be saved due to a technical issue — let's try that again."

        # Remember the ticket so a photo sent later in the call can attach to it.
        ud.booking_id = booking_id
        ud.booking_badges = badges
        context.userdata.customer_name = customer_name
        context.userdata.customer_phone = customer_phone
        context.userdata.customer_email = customer_email
        context.userdata.booked_appointment = {
            "start_time": arrive_label,
            "day": day_label,
            "customer_name": customer_name,
            "store": store,
        }

        message = (
            f"Booked {vehicle_text} for {customer_name} at {arrive_label} {day_label} "
            f"at our Alpine View store, {STORE_ADDRESS}."
        )
        if add_on_items:
            message += f" Added while it's in: {add_ons_text}."
        if offer:
            message += f" Coupon applied: {offer}."

        try:
            job_ctx = get_job_context()
            await job_ctx.room.local_participant.send_text(message, topic=CHAT_TOPIC)
        except Exception:
            logger.exception("failed to post booking confirmation to chat")

        if customer_email:
            try:
                await send_email_smtp(
                    to=customer_email,
                    subject="Your Midas appointment is booked",
                    body=message,
                )
            except Exception:
                logger.exception("failed to email booking confirmation")

        try:
            await send_whatsapp(to=customer_phone, body=message)
        except Exception:
            logger.exception("failed to send whatsapp booking confirmation")

        return message

    @function_tool
    async def record_callback(
        self,
        context: RunContext[ServiceAdvisorData],
        customer_name: str,
        customer_phone: str,
        service: str,
        preferred_day: str = "as soon as possible",
    ) -> str:
        """Log a callback request when the shop can't fit the caller in.

        Use this as the graceful fallback when there are genuinely no open bays
        in the days the caller can do (after check_service_availability comes
        back empty), instead of asking more questions. Collect and confirm the
        name and phone first. It puts the request on the ops feed so the desk can
        call them back.

        Args:
            customer_name: The customer's full name.
            customer_phone: The customer's phone number in E.164 format.
            service: What they wanted done, e.g. "brake inspection".
            preferred_day: When they'd ideally like to come in, in their words, e.g. "tomorrow morning" or "any day next week".
        """
        if len(_phone_digits(customer_phone)) < 10:
            raise ToolError(
                "that phone number is too short — ask the caller to repeat it, "
                "with the area code."
            )

        await context.update("Okay, let me take your details for a callback.")
        logged = await dashboard.record_call(
            store=DEMO_STORE,
            intent="Callback",
            summary=f"{customer_name} — {service}; prefers {preferred_day}",
            outcome="Callback requested",
            outcome_type="info",
            extra=customer_phone,
        )
        if not logged:
            return (
                "I couldn't log that just now — let's try taking your details "
                "again, or you can call the shop directly."
            )

        context.userdata.customer_name = customer_name
        context.userdata.customer_phone = customer_phone
        return (
            f"Got it — I've put {customer_name} down for a callback about the "
            f"{service}. Someone from the shop will reach out to book a time."
        )

    @function_tool
    async def send_location(
        self,
        context: RunContext[ServiceAdvisorData],
        location_query: str,
        customer_email: str | None = None,
        customer_phone: str | None = None,
    ) -> str:
        """Send a Google Maps link for one of our US service center locations.

        Only covers our fixed set of US locations. Match `location_query` against
        what the caller said (e.g. a city name). The link is always posted to the
        call's chat. Pass `customer_email` and/or `customer_phone` too if the user
        has given them and wants the link emailed and/or texted as well.

        Args:
            location_query: The city or location name the user mentioned.
            customer_email: The user's email address, if they want the link emailed too.
            customer_phone: The user's US phone number in E.164 format (e.g. +15125550100), if they want the link texted too.
        """
        location = find_location(location_query)
        if location is None:
            return f"No listed US location matches '{location_query}'."

        link = maps_link(location.address)
        message = f"{location.name}: {location.address}\n{link}"

        try:
            job_ctx = get_job_context()
            await job_ctx.room.local_participant.send_text(message, topic=CHAT_TOPIC)
        except Exception:
            logger.exception("failed to send location to chat")

        sent_via = ["chat"]

        if customer_email:
            try:
                await send_email_smtp(
                    to=customer_email,
                    subject=f"Directions to our {location.name} location",
                    body=message,
                )
                sent_via.append("email")
            except Exception:
                logger.exception("failed to email location")

        if customer_phone:
            try:
                await send_sms(to=customer_phone, body=message)
                sent_via.append("text message")
            except Exception:
                logger.exception("failed to text location")

        return (
            f"I've sent the {location.name} map link via "
            + " and ".join(sent_via)
            + "."
        )


async def _handle_uploaded_photo(
    reader: "rtc.ByteStreamReader",
    participant_identity: str,
    session: AgentSession[ServiceAdvisorData],
) -> None:
    """Analyze a photo the caller sent via the in-call capture button.

    This is push-based (triggered by the user, not a tool call) and
    registered once at the room level. The result is spoken through the
    active agent when it arrives.
    """
    chunks = bytearray()
    async for chunk in reader:
        chunks.extend(chunk)
    mime_type = reader.info.mime_type or "image/jpeg"
    image_bytes = bytes(chunks)

    try:
        analysis = await analyze_vehicle_photo(
            image_bytes=image_bytes, mime_type=mime_type
        )
    except Exception:
        logger.exception("failed to analyze uploaded photo")
        await session.generate_reply(
            instructions=(
                "Let the caller know the photo they sent couldn't be analyzed "
                "due to a technical issue."
            )
        )
        return

    session.userdata.photo_analyses.append(analysis)

    try:
        photo_url = await store_photo(
            image_bytes=image_bytes,
            mime_type=mime_type,
            participant_identity=participant_identity,
            analysis=analysis,
        )
        if photo_url:
            ud = session.userdata
            ud.photo_urls.append(photo_url)
            # If a ticket already exists for this call, attach the new photo to
            # it now (the shop board listens for booking updates). Photos sent
            # before booking are already carried in at booking time.
            if ud.booking_id:
                badges = ud.booking_badges or ["AI"]
                if "PHOTO" not in badges:
                    badges = [*badges, "PHOTO"]
                await dashboard.update_booking(
                    ud.booking_id,
                    {"photo_urls": ud.photo_urls, "badges": badges},
                )
                ud.booking_badges = badges
    except Exception:
        # Non-fatal: a storage failure shouldn't block sharing the analysis
        # with the caller — it just means this photo won't show on the shop
        # board later.
        logger.exception("failed to store uploaded photo")

    await session.generate_reply(
        instructions=(
            f"The caller just sent a photo. Here is what the vision analysis "
            f"found: {analysis}\n\nShare this with them conversationally, in "
            "one to three sentences, and ask a natural follow-up if relevant."
        )
    )


server = AgentServer()


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    # Logging setup
    # Add any other context you want in all log entries here
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # The agent carries its own models — a Deepgram + OpenAI + Cartesia
    # STT-LLM-TTS pipeline. The session itself stays model-agnostic.
    #
    # Turn-taking runs on Deepgram Flux (docs: Deepgram STT > Turn detection):
    #  - turn_detection="stt": Flux's phrase-endpointing model decides end of
    #    turn from both acoustic and semantic cues, so mid-thought pauses aren't
    #    treated as done. The bundled VAD still handles interruption detection.
    #  - endpointing 0.5s min / 3.0s max: the documented default delays applied
    #    on top of Flux's end-of-turn signal (the old 0.4s floor made the agent
    #    jump in on natural pauses).
    #  - adaptive interruption: distinguishes the caller cutting in from mere
    #    backchannel ("uh-huh") using an audio model.
    #  - preemptive generation + TTS keep replies fast: Flux's eager end-of-turn
    #    events (eager_eot_threshold on the STT) start generation during the
    #    confirmation window; playback stays gated on turn confirmation, so this
    #    never talks over the caller.
    session = AgentSession[ServiceAdvisorData](
        userdata=ServiceAdvisorData(),
        turn_handling=TurnHandlingOptions(
            turn_detection="stt",
            endpointing={"min_delay": 0.5, "max_delay": 3.0},
            interruption={"mode": "adaptive", "min_duration": 0.5, "min_words": 0},
            preemptive_generation={"enabled": True, "preemptive_tts": True},
        ),
    )

    # Keep references so these tasks aren't garbage-collected mid-flight.
    _photo_tasks: set[asyncio.Task] = set()

    def _on_photo_stream(
        reader: "rtc.ByteStreamReader", participant_identity: str
    ) -> None:
        task = asyncio.create_task(
            _handle_uploaded_photo(reader, participant_identity, session)
        )
        _photo_tasks.add(task)
        task.add_done_callback(_photo_tasks.discard)

    # Registered once at the room level so a caller can send a photo during any
    # part of the call.
    ctx.room.register_byte_stream_handler(PHOTO_TOPIC, _on_photo_stream)

    # Start the session, which initializes the voice pipeline and warms up the models
    await session.start(
        agent=ServiceAdvisorAgent(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                # Full-size voice-isolation model (LiveKit's recommended pick) —
                # cleans the input before VAD/STT/turn detection see it.
                noise_cancellation=ai_coustics.audio_enhancement(
                    model=ai_coustics.EnhancerModel.QUAIL_VF_L
                ),
            ),
        ),
    )

    # Join the room and connect to the user
    await ctx.connect()

    # Ambient office noise + occasional keyboard typing while the agent looks
    # things up, so the call sounds like a real service center front desk.
    background_audio = BackgroundAudioPlayer(
        # Front-desk room tone, turned up so it actually reads under the voice,
        # with a 2s fade-in so it eases in instead of popping on.
        ambient_sound=AudioConfig(
            BuiltinAudioClip.OFFICE_AMBIENCE, volume=1.0, fade_in=2.0
        ),
        thinking_sound=[
            AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING, volume=0.7, probability=0.6),
            AudioConfig(BuiltinAudioClip.KEYBOARD_TYPING2, volume=0.7, probability=0.4),
        ],
    )
    # Log the outcome so the deploy logs confirm the ambience track actually
    # started (vs. failing silently) — the caller not hearing it is otherwise
    # hard to tell apart from a playback issue on the frontend side.
    try:
        await background_audio.start(room=ctx.room, agent_session=session)
        logger.info("background audio started (office ambience, volume 1.0)")
    except Exception:
        logger.exception("background audio failed to start")

    async def _shutdown_cleanup() -> None:
        # Cancel any in-flight photo analyses so they can't hold the process open.
        for task in list(_photo_tasks):
            task.cancel()
        # Close background audio, but cap it: a stuck audio-track teardown must
        # not stall the ~10s shutdown window and get the process force-killed
        # (the "process did not exit in time, killing process" error).
        try:
            await asyncio.wait_for(background_audio.aclose(), timeout=5.0)
        except Exception:
            logger.warning("background audio didn't close cleanly at shutdown")

    ctx.add_shutdown_callback(_shutdown_cleanup)


if __name__ == "__main__":
    cli.run_app(server)

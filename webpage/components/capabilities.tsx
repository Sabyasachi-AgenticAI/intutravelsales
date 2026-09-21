import { Container } from './container';
import { Reveal } from './reveal';

const FEATURES = [
  {
    tag: 'Voice',
    title: 'Natural, human-paced calls',
    body: 'Handles interruptions, follow-up questions, and real conversation — not a rigid menu tree. It waits for you to actually finish a thought before it answers.',
    c: 'var(--violet)',
    bg: 'var(--violet-bg)',
  },
  {
    tag: 'Booking',
    title: 'Live appointment booking',
    body: "Checks the shop's real bay schedule — today or weeks out — and books the open slot while the caller is still on the line. No double-booking, no past-due times.",
    c: 'var(--magenta)',
    bg: 'var(--magenta-bg)',
  },
  {
    tag: 'Diagnostics',
    title: 'Vehicle & fault-code grounding',
    body: "Decodes a VIN, checks open recalls, and matches symptoms to likely causes — real service knowledge, not a script that only knows hours and pricing.",
    c: 'var(--teal)',
    bg: 'var(--teal-bg)',
  },
  {
    tag: 'Upsell',
    title: 'Reason-first recommendations',
    body: "Suggests one genuinely relevant add-on with an honest reason — never just because there's a coupon — and only when the caller isn't stressed or in a hurry.",
    c: 'var(--amber)',
    bg: 'var(--amber-bg)',
  },
  {
    tag: 'Confirmation',
    title: 'Instant multi-channel confirmation',
    body: 'Text, WhatsApp, and email the moment the appointment is booked, with the shop address and directions if they want them.',
    c: 'var(--coral)',
    bg: 'var(--coral-bg)',
  },
  {
    tag: 'Handoff',
    title: 'Live human handoff',
    body: "Routes straight to a person for anything safety-critical, or whenever a caller needs one — it knows the line between what it can handle and what a human should.",
    c: 'var(--violet-soft)',
    bg: 'var(--violet-bg)',
  },
];

export function Capabilities() {
  return (
    <section id="product" className="py-24 md:py-28">
      <Container>
        <Reveal className="max-w-[640px]">
          <div className="eyebrow">The Product</div>
          <h2 className="mt-4 text-[2rem] font-extrabold tracking-tight text-[var(--ink)] sm:text-[2.5rem]">
            Smarter than voicemail. Faster than your front desk.
          </h2>
          <p className="mt-4 text-[16px] text-[var(--ink-dim)]">
            intuService is grounded in real vehicle and service knowledge — not a script tree. It
            answers the way a good service advisor would, on every single call.
          </p>
        </Reveal>

        <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <Reveal key={f.title} delay={i * 60}>
              <div
                className="h-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] p-7 transition-colors hover:border-[var(--line-strong)] hover:bg-[var(--surface-hover)]"
                style={{ borderTopColor: f.c, borderTopWidth: '2.5px' }}
              >
                <span
                  className="inline-block rounded-full px-2.5 py-1 font-[family-name:var(--font-data)] text-[11px] tracking-[0.06em] uppercase"
                  style={{ color: f.c, background: f.bg }}
                >
                  {f.tag}
                </span>
                <h3 className="mt-4 text-[17px] font-bold text-[var(--ink)]">{f.title}</h3>
                <p className="mt-2.5 text-[14px] text-[var(--ink-dim)]">{f.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  );
}

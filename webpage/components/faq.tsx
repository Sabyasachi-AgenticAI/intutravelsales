import { Container } from './container';
import { Reveal } from './reveal';

const FAQS = [
  {
    q: 'Does this replace my front desk staff?',
    a: 'No. intuService handles overflow, after-hours, and busy-signal calls, and can hand off to your team live during business hours whenever a caller needs a person.',
  },
  {
    q: 'Does it work with my current shop management system?',
    a: 'Yes. intuService is built to sit alongside Tekmetric, Shop-Ware, Mitchell 1, or a standalone calendar — it does not require replacing anything you already use.',
  },
  {
    q: 'What happens after the free trial?',
    a: "You choose the plan that fits your call volume, or stay on Pay-As-You-Go with no commitment. There's no auto-upgrade and no setup fee either way.",
  },
  {
    q: 'Is job coordination or inventory management available now?',
    a: 'Not yet — those are future stages of the platform, built once the AI Receptionist has proven itself in your shop. No pricing or commitment applies to them today.',
  },
  {
    q: 'What does intuService sound like?',
    a: "Natural and conversational, not a script tree — it understands follow-up questions the way a service advisor would. Hear it yourself in the live demo above.",
  },
];

export function FAQ() {
  return (
    <section id="faq" className="border-t border-[var(--line)] bg-[var(--ground-soft)]/60 py-24">
      <Container>
        <Reveal className="max-w-[640px]">
          <div className="eyebrow">Questions</div>
          <h2 className="mt-4 text-[2rem] font-extrabold tracking-tight text-[var(--ink)] sm:text-[2.5rem]">
            Frequently asked
          </h2>
        </Reveal>

        <Reveal delay={80} className="mt-10 max-w-[760px]">
          {FAQS.map((f, i) => (
            <details
              key={f.q}
              open={i === 0}
              className="group border-b border-[var(--line)] py-5"
            >
              <summary className="flex cursor-pointer list-none items-center justify-between text-[15.5px] font-semibold text-[var(--ink)]">
                {f.q}
                <span className="ml-4 shrink-0 text-[20px] leading-none text-[var(--magenta)] transition-transform group-open:rotate-45">
                  +
                </span>
              </summary>
              <p className="mt-3.5 pr-8 text-[14px] text-[var(--ink-dim)]">{f.a}</p>
            </details>
          ))}
        </Reveal>
      </Container>
    </section>
  );
}

import { Container } from './container';
import { Reveal } from './reveal';

const STEPS = [
  {
    n: '01',
    title: 'Connect your line',
    body: 'Shop hours, pricing, and services loaded in. No hardware to install, no phone swap.',
  },
  {
    n: '02',
    title: 'Shadow mode',
    body: 'intuService runs alongside your current line so nothing changes for customers yet.',
  },
  {
    n: '03',
    title: 'Go live',
    body: 'Full coverage, with daily call review while your team gets comfortable with it.',
  },
  {
    n: '04',
    title: 'Track & tune',
    body: 'A weekly summary of calls answered, jobs booked, and revenue recovered.',
  },
];

export function HowItWorks() {
  return (
    <section id="how" className="border-y border-[var(--line)] bg-[var(--ground-soft)]/60 py-24">
      <Container>
        <Reveal className="max-w-[640px]">
          <div className="eyebrow">Getting Live</div>
          <h2 className="mt-4 text-[2rem] font-extrabold tracking-tight text-[var(--ink)] sm:text-[2.5rem]">
            From first call to full coverage in two weeks.
          </h2>
        </Reveal>

        <div className="mt-14 grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          {STEPS.map((s, i) => (
            <Reveal key={s.n} delay={i * 70}>
              <div className="border-l-2 border-[var(--violet)] pl-5">
                <span className="font-[family-name:var(--font-data)] text-[11px] tracking-[0.1em] text-[var(--ink-faint)] uppercase">
                  Call log {s.n}
                </span>
                <h3 className="mt-3 text-[17px] font-bold text-[var(--ink)]">{s.title}</h3>
                <p className="mt-2 text-[14px] text-[var(--ink-dim)]">{s.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  );
}

import { Container } from './container';
import { Reveal } from './reveal';

const STAGES = [
  {
    title: 'Work Order Coordination',
    body: 'Automated technician assignment and job status tracking, layered on your existing shop management system — bay scheduling itself is already live in the AI Service Advisor.',
    c: 'var(--teal)',
  },
  {
    title: 'Inventory & Parts Management',
    body: 'Automated parts availability checks and reorder triggers tied to the jobs actually on your board.',
    c: 'var(--magenta)',
  },
  {
    title: 'Warranty & DVI Follow-Up',
    body: 'Automated follow-up on inspection findings and warranty claim status.',
    c: 'var(--amber)',
  },
];

export function Roadmap() {
  return (
    <section id="roadmap" className="relative overflow-hidden py-24 md:py-28">
      <div
        aria-hidden
        className="absolute inset-0 -z-10 opacity-[0.85]"
        style={{ background: 'linear-gradient(180deg, var(--twilight-2), var(--ground))' }}
      />
      <Container>
        <Reveal className="max-w-[640px]">
          <div className="eyebrow">The Platform</div>
          <h2 className="mt-4 text-[2rem] font-extrabold tracking-tight text-[var(--ink)] sm:text-[2.5rem]">
            The AI Service Advisor is Stage 1.
          </h2>
          <p className="mt-4 text-[16px] text-[var(--ink-dim)]">
            intuService is built to grow into the rest of shop operations — on your timeline, not
            ours. These aren&apos;t priced or scoped yet; they become real conversations once
            Stage 1 is proven in your shop.
          </p>
        </Reveal>

        <div className="mt-14 grid gap-5 md:grid-cols-3">
          {STAGES.map((s, i) => (
            <Reveal key={s.title} delay={i * 70}>
              <div className="h-full rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] p-7">
                <span
                  className="inline-block rounded-full border px-2.5 py-1 font-[family-name:var(--font-data)] text-[10.5px] tracking-[0.08em] uppercase"
                  style={{ color: s.c, borderColor: 'var(--line-strong)' }}
                >
                  Future stage
                </span>
                <h3 className="mt-4 text-[17px] font-bold text-[var(--ink)]">{s.title}</h3>
                <p className="mt-2.5 text-[14px] text-[var(--ink-dim)]">{s.body}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </Container>
    </section>
  );
}

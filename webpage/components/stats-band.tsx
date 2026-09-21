import { Container } from './container';

const STATS = [
  { num: '80%', label: 'of callers who hit voicemail never leave one', c: 'var(--coral)' },
  { num: '85%', label: "of those callers don't try calling back", c: 'var(--magenta)' },
  { num: '1 in 3', label: 'customers now expect to book online, not on hold', c: 'var(--teal)' },
  { num: '24/7', label: 'intuService answers — nights, weekends, holidays', c: 'var(--amber)' },
];

export function StatsBand() {
  return (
    <div className="border-b border-[var(--line)] bg-black/30">
      <Container className="grid grid-cols-2 gap-px overflow-hidden rounded-[var(--radius-sm)] bg-[var(--line)] md:grid-cols-4">
        {STATS.map((s) => (
          <div key={s.label} className="bg-[var(--ground)] px-7 py-10">
            <div className="text-[2.6rem] leading-none font-extrabold" style={{ color: s.c }}>
              {s.num}
            </div>
            <div className="mt-2.5 max-w-[190px] text-[13.5px] text-[var(--ink-dim)]">
              {s.label}
            </div>
          </div>
        ))}
      </Container>
      <Container className="py-4">
        <p className="font-[family-name:var(--font-data)] text-[11.5px] text-[var(--ink-faint)]">
          Industry figures on missed-call behavior, cited for context — not intuService-specific
          results.
        </p>
      </Container>
    </div>
  );
}

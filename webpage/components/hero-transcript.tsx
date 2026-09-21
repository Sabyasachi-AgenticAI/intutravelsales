'use client';

import { useEffect, useState } from 'react';

// Each turn reveals as one complete bubble, and — unlike a CSS opacity-only
// reveal — not-yet-arrived turns aren't rendered at all, so there's never a
// reserved blank gap in the transcript. Whatever frame you catch always reads
// as a normal, in-progress conversation.
const TRANSCRIPT = [
  { who: 'caller', text: 'My brakes have been squeaking for a few days now.' },
  { who: 'agent', text: 'Hmm — does it happen every time you brake, or only sometimes?' },
  { who: 'caller', text: 'Pretty much every time at this point.' },
  { who: 'agent', text: "Okay, that's worth a look — I've got 2:30 open today. Book it?" },
  { who: 'caller', text: 'Yes, please!' },
  { who: 'agent', text: "Perfect, you're all set.", chip: '✓ Booked · 2:30 PM' },
] as const;

const TURN_INTERVAL_MS = 1300;
const HOLD_AFTER_LAST_MS = 3200;
const RESET_PAUSE_MS = 900;

export function HeroTranscript() {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    function step(n: number) {
      if (cancelled) return;
      setCount(n);
      if (n < TRANSCRIPT.length) {
        timer = setTimeout(() => step(n + 1), TURN_INTERVAL_MS);
      } else {
        timer = setTimeout(() => {
          if (cancelled) return;
          setCount(0);
          timer = setTimeout(() => step(1), RESET_PAUSE_MS);
        }, HOLD_AFTER_LAST_MS);
      }
    }

    timer = setTimeout(() => step(1), 500);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, []);

  const visible = TRANSCRIPT.slice(0, count);

  return (
    <div className="w-full max-w-[400px] overflow-hidden rounded-[var(--radius)] border border-[var(--line-strong)] bg-[var(--ground-soft)]/90 shadow-[0_40px_90px_-30px_rgba(0,0,0,0.7)] backdrop-blur-xl">
      <div className="flex items-center justify-between border-b border-[var(--line)] px-5 py-4">
        <span className="flex items-center gap-2.5 font-[family-name:var(--font-data)] text-[12px] tracking-wide text-[var(--ink-dim)] uppercase">
          <span
            className="inline-block h-2 w-2 rounded-full bg-[var(--good)]"
            style={{
              animationName: 'pulse-dot',
              animationDuration: '1.8s',
              animationTimingFunction: 'ease-in-out',
              animationIterationCount: 'infinite',
            }}
          />
          Live call
        </span>
        <span className="font-[family-name:var(--font-data)] text-[11px] text-[var(--ink-faint)]">
          intuService AI
        </span>
      </div>

      <div className="flex min-h-[262px] flex-col justify-end gap-2.5 px-5 py-5">
        {visible.map((turn, i) => (
          <div
            key={i}
            className={`flex flex-col ${turn.who === 'agent' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[84%] rounded-[14px] px-3.5 py-2.5 text-[13px] leading-snug ${
                turn.who === 'agent'
                  ? 'rounded-tr-[4px] bg-gradient-to-br from-[var(--violet)] to-[var(--magenta)] text-white'
                  : 'rounded-tl-[4px] border border-[var(--line)] bg-[var(--surface)] text-[var(--ink)]'
              }`}
            >
              {turn.text}
            </div>
            {'chip' in turn && turn.chip && (
              <span
                className="mt-1.5 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-[family-name:var(--font-data)] text-[10.5px] font-semibold tracking-wide"
                style={{ color: 'var(--amber-soft)', background: 'var(--amber-bg)' }}
              >
                {turn.chip}
              </span>
            )}
          </div>
        ))}
      </div>

      <div className="flex justify-between border-t border-[var(--line)] bg-black/20 px-5 py-3 font-[family-name:var(--font-data)] text-[11px] text-[var(--ink-faint)]">
        <span>Alex Reed · 2019 Honda Civic</span>
        <span>0:41</span>
      </div>
    </div>
  );
}

'use client';

import { useState } from 'react';
import { Container } from './container';
import { Reveal } from './reveal';

const MONTH_LABEL = 'June 2026';
const WEEKDAYS = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];
const WEEKS: (number | null)[][] = [
  [null, 1, 2, 3, 4, 5, 6],
  [7, 8, 9, 10, 11, 12, 13],
  [14, 15, 16, 17, 18, 19, 20],
  [21, 22, 23, 24, 25, 26, 27],
  [28, 29, 30, null, null, null, null],
];
const TODAY = 17;
const AVAILABLE_DAYS = new Set([15, 16, 17, 18, 19, 22, 23, 24, 25, 26]);

const SLOTS = [
  { time: '9:00 AM', bay: 'Bay 1', service: 'Oil change' },
  { time: '9:30 AM', bay: 'Alignment Rack', service: 'Alignment' },
  { time: '10:30 AM', bay: 'Bay 2', service: 'Brake inspection' },
  { time: '11:00 AM', bay: 'Bay 3', service: 'Diagnostic' },
  { time: '1:00 PM', bay: 'Bay 1', service: 'Tire rotation' },
  { time: '2:30 PM', bay: 'Bay 2', service: 'Fluid flush' },
];

export function ScheduleShowcase() {
  const [selectedDay, setSelectedDay] = useState(TODAY);
  const [selectedSlot, setSelectedSlot] = useState<number | null>(2);

  return (
    <section className="py-24 md:py-28">
      <Container className="grid items-center gap-14">
        <Reveal>
          <div className="eyebrow">Under the Hood</div>
          <h2 className="mt-4 text-[2rem] font-extrabold tracking-tight text-[var(--ink)] sm:text-[2.5rem]">
            It books into a real bay, not a guess.
          </h2>
          <p className="mt-4 max-w-[440px] text-[16px] text-[var(--ink-dim)]">
            Every slot intuService offers on a call is checked against the shop&apos;s live bay
            schedule first — so what it books is what actually shows up on the board your team
            works from.
          </p>
          <ul className="mt-7 space-y-3 text-[14px] text-[var(--ink-dim)]">
            <li className="flex gap-2.5">
              <span className="mt-1 h-1.5 w-1.5 flex-none rounded-full bg-[var(--violet)]" />
              Never double-books a bay, never offers a time that&apos;s already passed
            </li>
            <li className="flex gap-2.5">
              <span className="mt-1 h-1.5 w-1.5 flex-none rounded-full bg-[var(--teal)]" />
              Sizes each job by service type, so the board stays realistic
            </li>
            <li className="flex gap-2.5">
              <span className="mt-1 h-1.5 w-1.5 flex-none rounded-full bg-[var(--amber)]" />
              Same-day or weeks out — the schedule it reads from is always current
            </li>
          </ul>
        </Reveal>

        <Reveal delay={80}>
          <div className="mx-auto w-full max-w-[640px] overflow-hidden rounded-[var(--radius)] border border-[var(--line-strong)] bg-[var(--ground-soft)]/90 shadow-[0_40px_90px_-30px_rgba(0,0,0,0.7)] backdrop-blur-xl">
            <div className="flex items-center justify-between border-b border-[var(--line)] px-6 py-4">
              <span className="flex items-center gap-2.5 font-[family-name:var(--font-data)] text-[11.5px] tracking-wide text-[var(--ink-dim)] uppercase">
                <span
                  className="h-2 w-2 rounded-full bg-[var(--good)]"
                  style={{
                    animationName: 'pulse-dot',
                    animationDuration: '1.8s',
                    animationTimingFunction: 'ease-in-out',
                    animationIterationCount: 'infinite',
                  }}
                />
                Book a bay
              </span>
              <span className="font-[family-name:var(--font-data)] text-[11px] text-[var(--ink-faint)]">
                Springfield Auto · 30 min
              </span>
            </div>

            <div className="grid gap-8 p-6 sm:grid-cols-[1.1fr_1fr] sm:p-7">
                  {/* month calendar */}
                  <div>
                    <div className="mb-4 flex items-center justify-between">
                      <span className="text-[13.5px] font-semibold text-[var(--ink)]">{MONTH_LABEL}</span>
                      <div className="flex gap-1">
                        <span className="flex h-6 w-6 items-center justify-center rounded-full border border-[var(--line)] text-[12px] text-[var(--ink-faint)]">
                          ‹
                        </span>
                        <span className="flex h-6 w-6 items-center justify-center rounded-full border border-[var(--line)] text-[12px] text-[var(--ink-faint)]">
                          ›
                        </span>
                      </div>
                    </div>
                    <div className="grid grid-cols-7 gap-y-1.5 text-center">
                      {WEEKDAYS.map((w, i) => (
                        <span
                          key={i}
                          className="font-[family-name:var(--font-data)] text-[10px] text-[var(--ink-faint)] uppercase"
                        >
                          {w}
                        </span>
                      ))}
                      {WEEKS.flat().map((d, i) => {
                        if (!d) return <span key={i} />;
                        const available = AVAILABLE_DAYS.has(d);
                        const selected = d === selectedDay;
                        return (
                          <button
                            key={i}
                            disabled={!available}
                            onClick={() => setSelectedDay(d)}
                            className="relative mx-auto flex h-8 w-8 items-center justify-center rounded-full text-[12.5px] font-medium transition-colors disabled:cursor-not-allowed"
                            style={
                              selected
                                ? {
                                    background: 'linear-gradient(135deg, var(--violet), var(--magenta))',
                                    color: 'white',
                                  }
                                : available
                                  ? { color: 'var(--ink)' }
                                  : { color: 'var(--ink-faint)', opacity: 0.4 }
                            }
                          >
                            {d}
                            {available && !selected && (
                              <span
                                className="absolute bottom-0.5 h-[3px] w-[3px] rounded-full"
                                style={{ background: 'var(--teal)' }}
                              />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* time slots */}
                  <div>
                    <span className="font-[family-name:var(--font-data)] text-[10.5px] tracking-[0.08em] text-[var(--ink-faint)] uppercase">
                      Available times
                    </span>
                    <div className="mt-3 flex flex-col gap-2">
                      {SLOTS.map((s, i) => {
                        const selected = i === selectedSlot;
                        return (
                          <button
                            key={s.time}
                            onClick={() => setSelectedSlot(i)}
                            className="flex items-center justify-between rounded-[var(--radius-sm)] border px-3.5 py-2.5 text-left text-[13px] font-semibold transition-colors"
                            style={
                              selected
                                ? {
                                    background: 'linear-gradient(135deg, var(--violet), var(--magenta))',
                                    borderColor: 'transparent',
                                    color: 'white',
                                  }
                                : {
                                    borderColor: 'var(--line)',
                                    color: 'var(--ink)',
                                    background: 'var(--surface)',
                                  }
                            }
                          >
                            {s.time}
                            <span
                              className="font-[family-name:var(--font-data)] text-[10px] font-medium tracking-wide uppercase"
                              style={{ color: selected ? 'rgba(255,255,255,0.8)' : 'var(--ink-faint)' }}
                            >
                              {s.bay}
                            </span>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>

            <div className="border-t border-[var(--line)] bg-black/20 px-6 py-3 text-center font-[family-name:var(--font-data)] text-[11px] text-[var(--ink-faint)]">
              Illustrative — the same board shape intuService books real appointments into.
            </div>
          </div>
        </Reveal>
      </Container>
    </section>
  );
}

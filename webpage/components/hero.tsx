'use client';

import { Container } from './container';
import { useDemoModal } from './demo-modal';
import { HeroTranscript } from './hero-transcript';
import { PillButton } from './pill-button';

export function Hero() {
  const { open } = useDemoModal();

  return (
    <header className="relative overflow-hidden border-b border-[var(--line)]">
      {/* atmospheric multi-hue gradient — our own brand violet, plus a magenta
          and amber partner, not a literal copy of any reference site's colors */}
      <div
        aria-hidden
        className="absolute inset-0 -z-10"
        style={{
          background:
            'radial-gradient(120% 70% at 50% -10%, var(--twilight-1) 0%, var(--twilight-2) 45%, var(--ground) 78%)',
        }}
      />
      <div
        aria-hidden
        className="absolute -top-32 left-[8%] -z-10 h-[460px] w-[560px] rounded-full opacity-45 blur-[110px]"
        style={{ background: 'var(--violet)', animation: 'drift 14s ease-in-out infinite' }}
      />
      <div
        aria-hidden
        className="absolute -top-24 right-[6%] -z-10 h-[420px] w-[520px] rounded-full opacity-35 blur-[110px]"
        style={{ background: 'var(--magenta)', animation: 'drift 16s ease-in-out infinite reverse' }}
      />
      {/* a low, warm glow — "the lights are still on" after hours */}
      <div
        aria-hidden
        className="absolute bottom-0 left-1/2 -z-10 h-[220px] w-[900px] -translate-x-1/2 rounded-full opacity-[0.20] blur-[100px]"
        style={{ background: 'var(--amber)' }}
      />

      <Container className="grid items-center gap-16 pt-28 pb-24 md:pt-36 md:pb-32">
        <div className="text-center">
          <div className="eyebrow justify-center">AI Service Advisor for Auto Repair Shops</div>
          <h1 className="mt-6 text-[2.6rem] leading-[1.05] font-extrabold tracking-tight text-[var(--ink)] sm:text-[3.4rem] lg:text-[3.75rem]">
            Every missed call is{' '}
            <span className="bg-gradient-to-r from-[var(--violet-soft)] via-[var(--magenta-soft)] to-[var(--amber-soft)] bg-clip-text text-transparent">
              a repair order — waiting to happen.
            </span>
          </h1>
          <p className="mx-auto mt-6 max-w-[480px] text-[17px] text-[var(--ink-dim)]">
            intuService answers instantly, triages the problem like a real advisor, books the
            appointment on today&apos;s actual schedule, and texts the confirmation — before the
            team even sees a voicemail.
          </p>
          <div className="mt-9 flex flex-col items-center gap-3.5 sm:flex-row sm:justify-center">
            <PillButton href="#demo">Talk to it right now</PillButton>
            <PillButton onClick={() => open('demo')} variant="ghost">
              Get a demo
            </PillButton>
          </div>
          <div className="mt-5 font-[family-name:var(--font-data)] text-[11.5px] tracking-[0.08em] text-[var(--ink-faint)] uppercase">
            Seamless Integration · Live in Weeks
          </div>
        </div>

        {/* floating dark "product UI" card — a live call transcript, filling in
            turn by turn. Only arrived turns are rendered (see HeroTranscript),
            so there's never a reserved blank gap for a turn that hasn't landed
            yet — any frame you catch reads as a real in-progress conversation. */}
        <div className="flex justify-center">
          <HeroTranscript />
        </div>
      </Container>
    </header>
  );
}

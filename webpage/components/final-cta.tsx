'use client';

import { Container } from './container';
import { useDemoModal } from './demo-modal';
import { PillButton } from './pill-button';
import { Reveal } from './reveal';

export function FinalCTA() {
  const { open } = useDemoModal();

  return (
    <section className="relative overflow-hidden py-28 text-center">
      <div
        aria-hidden
        className="absolute inset-0 -z-10 opacity-[0.85]"
        style={{
          background:
            'radial-gradient(90% 90% at 50% 100%, var(--twilight-1), var(--ground) 65%)',
        }}
      />
      <div
        aria-hidden
        className="absolute bottom-[-10%] left-1/2 -z-10 h-[360px] w-[720px] -translate-x-1/2 rounded-full opacity-30 blur-[110px]"
        style={{ background: 'var(--magenta)' }}
      />
      <Container>
        <Reveal>
          <h2 className="mx-auto max-w-[720px] text-[2.2rem] font-extrabold tracking-tight text-[var(--ink)] sm:text-[2.75rem]">
            Stop losing customers to a ringing phone.
          </h2>
          <p className="mx-auto mt-4 max-w-[500px] text-[16px] text-[var(--ink-dim)]">
            15-day free trial. No setup fee. Live in two weeks.
          </p>
          <div className="mt-9 flex flex-col items-center justify-center gap-3.5 sm:flex-row">
            <PillButton href="#demo">Talk to it right now</PillButton>
            <PillButton onClick={() => open('demo')} variant="ghost">
              Get a demo
            </PillButton>
          </div>
        </Reveal>
      </Container>
    </section>
  );
}

import { Container } from './container';
import { Reveal } from './reveal';
import { VoiceDemo } from './voice-demo';

const POINTS = [
  { c: 'var(--violet)', t: 'This is the real thing', b: 'Not a mockup — you\'re talking to the same voice agent a shop\'s customers reach.' },
  { c: 'var(--magenta)', t: 'It listens like a person', b: "It waits for you to finish a thought before it answers, and doesn't talk over you." },
  { c: 'var(--teal)', t: 'Try a real scenario', b: '"My brakes are squeaking" or "I need an oil change tomorrow" both work.' },
];

export function LiveDemo({ agentName }: { agentName: string }) {
  return (
    <section id="demo" className="relative overflow-hidden border-y border-[var(--line)] py-24 md:py-28">
      <div
        aria-hidden
        className="absolute inset-0 -z-10"
        style={{
          background:
            'radial-gradient(90% 60% at 15% 20%, var(--violet-bg), transparent 60%), radial-gradient(90% 60% at 85% 80%, var(--magenta-bg), transparent 60%)',
        }}
      />
      <Container className="grid items-center gap-16">
        <Reveal>
          <div className="eyebrow">Try It Yourself</div>
          <h2 className="mt-4 text-[2rem] font-extrabold tracking-tight text-[var(--ink)] sm:text-[2.5rem]">
            Don&apos;t take our word for it. Call it.
          </h2>
          <p className="mt-4 max-w-[440px] text-[16px] text-[var(--ink-dim)]">
            This is a live connection to the actual intuService voice agent — the same one that
            answers real calls for a real shop. Say hello.
          </p>

          <div className="mt-9 space-y-5">
            {POINTS.map((p) => (
              <div key={p.t} className="flex gap-4">
                <span
                  className="mt-1.5 h-2.5 w-2.5 flex-none rounded-full"
                  style={{ background: p.c, boxShadow: `0 0 0 4px color-mix(in oklab, ${p.c} 20%, transparent)` }}
                />
                <div>
                  <div className="text-[14.5px] font-semibold text-[var(--ink)]">{p.t}</div>
                  <div className="mt-0.5 text-[13.5px] text-[var(--ink-dim)]">{p.b}</div>
                </div>
              </div>
            ))}
          </div>
        </Reveal>

        <Reveal delay={80} className="flex justify-center">
          <VoiceDemo agentName={agentName} />
        </Reveal>
      </Container>
    </section>
  );
}

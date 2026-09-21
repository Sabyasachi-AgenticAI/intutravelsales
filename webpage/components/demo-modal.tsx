'use client';

import { createContext, useContext, useState, type FormEvent } from 'react';
import { DEMO_RECIPIENTS } from '@/lib/contact';
import { PillButton } from './pill-button';

type ModalKind = 'demo' | 'sales';

type DemoModalContextValue = {
  open: (kind?: ModalKind) => void;
};

const DemoModalContext = createContext<DemoModalContextValue | null>(null);

export function useDemoModal() {
  const ctx = useContext(DemoModalContext);
  if (!ctx) throw new Error('useDemoModal must be used within DemoModalProvider');
  return ctx;
}

const COPY: Record<ModalKind, { eyebrow: string; title: string; subject: string }> = {
  demo: {
    eyebrow: 'Get a demo',
    title: 'See intuService on your shop.',
    subject: 'Demo request — intuService',
  },
  sales: {
    eyebrow: 'Multi-location',
    title: "Let's talk about your group.",
    subject: 'Multi-location inquiry — intuService',
  },
};

export function DemoModalProvider({ children }: { children: React.ReactNode }) {
  const [kind, setKind] = useState<ModalKind | null>(null);
  const [sent, setSent] = useState(false);

  const close = () => {
    setKind(null);
    setSent(false);
  };

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const data = new FormData(form);
    const activeKind = kind ?? 'demo';

    const lines = [
      `Name: ${data.get('firstName')} ${data.get('lastName')}`,
      `Work email: ${data.get('email')}`,
      `Shop name: ${data.get('shop') || '—'}`,
      `Locations: ${data.get('locations') || '—'}`,
      `How did you hear about us: ${data.get('source') || '—'}`,
    ].join('\n');

    const mailto = `mailto:${DEMO_RECIPIENTS}?subject=${encodeURIComponent(
      COPY[activeKind].subject
    )}&body=${encodeURIComponent(lines)}`;

    window.location.href = mailto;
    setSent(true);
  }

  return (
    <DemoModalContext.Provider value={{ open: (k = 'demo') => setKind(k) }}>
      {children}

      {kind && (
        <div
          className="fixed inset-0 z-[100] flex items-start justify-center overflow-y-auto bg-black/70 px-4 py-10 backdrop-blur-sm sm:items-center"
          onClick={close}
        >
          <div
            className="relative w-full max-w-[440px] rounded-[var(--radius)] border border-[var(--line-strong)] bg-[var(--ground-soft)] p-7 shadow-[0_30px_80px_-20px_rgba(0,0,0,0.6)]"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={close}
              aria-label="Close"
              className="absolute top-4 right-4 text-[20px] leading-none text-[var(--ink-faint)] transition-colors hover:text-[var(--ink)]"
            >
              ×
            </button>

            {!sent ? (
              <>
                <div className="eyebrow">{COPY[kind].eyebrow}</div>
                <h3 className="mt-3 text-[1.4rem] font-bold tracking-tight text-[var(--ink)]">
                  {COPY[kind].title}
                </h3>
                <p className="mt-1.5 text-[13.5px] text-[var(--ink-dim)]">
                  Tell us a bit about the shop and we&apos;ll reach out.
                </p>

                <form onSubmit={handleSubmit} className="mt-6 space-y-4">
                  <Field label="Work email" name="email" type="email" required />
                  <div className="grid grid-cols-2 gap-3">
                    <Field label="First name" name="firstName" required />
                    <Field label="Last name" name="lastName" required />
                  </div>
                  <Field label="Shop name" name="shop" />
                  <Field
                    label={kind === 'sales' ? 'Number of locations' : 'ZIP / postal code'}
                    name="locations"
                  />
                  <div>
                    <label className="mb-1.5 block text-[13px] font-medium text-[var(--ink-dim)]">
                      How did you hear about us?
                    </label>
                    <textarea
                      name="source"
                      rows={2}
                      className="w-full resize-none rounded-[var(--radius-sm)] border border-[var(--line)] bg-[var(--surface)] px-3.5 py-2.5 text-[14px] text-[var(--ink)] outline-none placeholder:text-[var(--ink-faint)] focus:border-[var(--line-strong)]"
                    />
                  </div>

                  <PillButton type="submit" className="w-full py-3">
                    Submit
                  </PillButton>
                  <p className="text-center text-[11.5px] text-[var(--ink-faint)]">
                    Opens your email client, addressed to our team.
                  </p>
                </form>
              </>
            ) : (
              <div className="py-6 text-center">
                <div className="eyebrow justify-center">Thanks</div>
                <h3 className="mt-3 text-[1.3rem] font-bold text-[var(--ink)]">
                  Your email client should be open.
                </h3>
                <p className="mt-2 text-[13.5px] text-[var(--ink-dim)]">
                  Didn&apos;t pop up? Reach us directly at{' '}
                  <a href={`mailto:${DEMO_RECIPIENTS}`} className="text-[var(--violet-soft)] underline">
                    contact@originalix.io
                  </a>
                  .
                </p>
                <PillButton variant="ghost" className="mt-6" onClick={close}>
                  Close
                </PillButton>
              </div>
            )}
          </div>
        </div>
      )}
    </DemoModalContext.Provider>
  );
}

function Field({
  label,
  name,
  type = 'text',
  required,
}: {
  label: string;
  name: string;
  type?: string;
  required?: boolean;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-[13px] font-medium text-[var(--ink-dim)]">
        {label}
        {required && <span className="text-[var(--coral)]"> *</span>}
      </label>
      <input
        name={name}
        type={type}
        required={required}
        className="w-full rounded-[var(--radius-sm)] border border-[var(--line)] bg-[var(--surface)] px-3.5 py-2.5 text-[14px] text-[var(--ink)] outline-none placeholder:text-[var(--ink-faint)] focus:border-[var(--line-strong)]"
      />
    </div>
  );
}

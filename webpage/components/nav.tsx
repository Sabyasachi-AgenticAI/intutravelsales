'use client';

import { Menu, X } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { Container } from './container';
import { useDemoModal } from './demo-modal';
import { PillButton } from './pill-button';
import { Wordmark } from './wordmark';

const LINKS = [
  { href: '#product', label: 'Product' },
  { href: '#demo', label: 'Try it live' },
  { href: '#pricing', label: 'Pricing' },
  { href: '#faq', label: 'FAQ' },
];

export function Nav() {
  const { open } = useDemoModal();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 border-b border-[var(--line)] bg-[var(--ground)]/85 backdrop-blur-md">
      <Container className="flex min-h-[68px] items-center justify-between py-3">
        <Link href="#" className="flex flex-col leading-none">
          <Wordmark className="text-[25px]" />
          <span className="mt-1 block bg-gradient-to-r from-[var(--teal-soft)] to-[var(--violet-soft)] bg-clip-text font-[family-name:var(--font-tagline)] text-[8.5px] font-medium tracking-[0.02em] text-transparent sm:text-[10px]">
            AI Service Advisor for Auto Repair Shops
          </span>
        </Link>

        <div className="hidden items-center gap-8 md:flex">
          {LINKS.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-[14px] font-medium text-[var(--ink-dim)] transition-colors hover:text-[var(--ink)]"
            >
              {l.label}
            </a>
          ))}
        </div>

        <div className="flex items-center gap-3">
          {/* Wrapped, not "hidden" passed straight into PillButton's own
              className — PillButton's base classes always include an
              unconditional "inline-flex", and cn() is a plain join with no
              conflict resolution, so "hidden" there can lose the cascade to
              it depending on Tailwind's stylesheet source order. */}
          <div className="hidden md:block">
            <PillButton onClick={() => open('demo')} className="px-5 py-2.5 text-[13.5px]">
              Get a demo
            </PillButton>
          </div>
          <button
            onClick={() => setMobileOpen((v) => !v)}
            aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileOpen}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-[var(--line)] text-[var(--ink)] md:hidden"
          >
            {mobileOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </Container>

      {mobileOpen && (
        <div className="border-t border-[var(--line)] bg-[var(--ground)] px-4 pt-2 pb-6 md:hidden">
          <div className="flex flex-col">
            {LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={() => setMobileOpen(false)}
                className="border-b border-[var(--line)] py-3.5 text-[15px] font-medium text-[var(--ink-dim)]"
              >
                {l.label}
              </a>
            ))}
          </div>
          <PillButton
            onClick={() => {
              setMobileOpen(false);
              open('demo');
            }}
            className="mt-5 w-full py-3 text-[13.5px]"
          >
            Get a demo
          </PillButton>
        </div>
      )}
    </nav>
  );
}

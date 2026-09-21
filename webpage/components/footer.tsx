import {
  CONTACT_ADDRESS,
  CONTACT_EMAIL,
  CONTACT_MAILTO,
  CONTACT_PHONE_DISPLAY,
  CONTACT_TEL,
  LINKEDIN_URL,
  WEBSITE_DISPLAY,
  WEBSITE_URL,
} from '@/lib/contact';
import { Container } from './container';
import { Wordmark } from './wordmark';

// Official LinkedIn "in" logo mark (brand blue square + white glyph),
// not a generic outline icon.
function LinkedInLogo() {
  return (
    <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden>
      <rect width="24" height="24" rx="4.5" fill="#0A66C2" />
      <path
        fill="#fff"
        d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.266 2.37 4.266 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452z"
      />
    </svg>
  );
}

const COLUMNS = [
  {
    title: 'Product',
    links: [
      { href: '#product', label: 'Features' },
      { href: '#how', label: 'How it works' },
      { href: '#roadmap', label: 'Roadmap' },
    ],
  },
  {
    title: 'Company',
    links: [
      { href: '#pricing', label: 'Pricing' },
      { href: '#faq', label: 'FAQ' },
      { href: '#', label: 'Contact' },
    ],
  },
  {
    title: 'Get Started',
    links: [
      { href: '#pricing', label: 'Start free trial' },
      { href: '#demo', label: 'Talk to it live' },
    ],
  },
];

export function Footer() {
  return (
    <footer className="bg-black/35 py-16 text-[var(--ink-faint)]">
      <Container>
        <div className="grid gap-10 border-b border-[var(--line)] pb-10 md:grid-cols-[1.4fr_repeat(3,1fr)]">
          <div>
            <Wordmark className="text-[19px]" />
            <p className="mt-3.5 max-w-[260px] text-[13.5px]">
              Agentic AI Service Advisor for auto repair shops — part of the AI Operating System
              for Garage Management Solutions.
            </p>
            <div className="mt-3 flex flex-col gap-1 font-[family-name:var(--font-data)] text-[11.5px] tracking-[0.04em] text-[var(--ink-faint)] uppercase">
              <a href={WEBSITE_URL} target="_blank" rel="noopener noreferrer" className="w-fit transition-colors hover:text-[var(--ink)]">
                {WEBSITE_DISPLAY}
              </a>
              <a href={CONTACT_TEL} className="w-fit transition-colors hover:text-[var(--ink)]">
                Call: {CONTACT_PHONE_DISPLAY}
              </a>
              <a href={CONTACT_MAILTO} className="w-fit normal-case transition-colors hover:text-[var(--ink)]">
                Email: {CONTACT_EMAIL}
              </a>
              <span>{CONTACT_ADDRESS}</span>
            </div>
            <a
              href={LINKEDIN_URL}
              target="_blank"
              rel="noopener noreferrer"
              aria-label="OriginalIX on LinkedIn"
              className="mt-4 inline-flex opacity-90 transition-opacity hover:opacity-100"
            >
              <LinkedInLogo />
            </a>
          </div>
          {COLUMNS.map((col) => (
            <div key={col.title}>
              <h4 className="mb-3.5 font-[family-name:var(--font-data)] text-[11.5px] tracking-[0.08em] text-[var(--ink-faint)] uppercase">
                {col.title}
              </h4>
              <ul className="space-y-2.5">
                {col.links.map((l) => (
                  <li key={l.label}>
                    <a
                      href={l.href}
                      className="text-[13.5px] text-[var(--ink-dim)] transition-colors hover:text-[var(--ink)]"
                    >
                      {l.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="flex flex-wrap justify-between gap-3 pt-6 text-[12px]">
          <span>© intuService {new Date().getFullYear()}. All rights reserved.</span>
          <span className="flex flex-wrap gap-x-2">
            <span>{CONTACT_ADDRESS}</span>
            <span aria-hidden>·</span>
            <a href={CONTACT_TEL} className="transition-colors hover:text-[var(--ink)]">
              {CONTACT_PHONE_DISPLAY}
            </a>
            <span aria-hidden>·</span>
            <a href={CONTACT_MAILTO} className="transition-colors hover:text-[var(--ink)]">
              contact@originalix.io
            </a>
          </span>
        </div>
      </Container>
    </footer>
  );
}

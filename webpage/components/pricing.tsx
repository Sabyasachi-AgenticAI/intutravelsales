'use client';

import { useState } from 'react';
import { Container } from './container';
import { useDemoModal } from './demo-modal';
import { PillButton } from './pill-button';
import { Reveal } from './reveal';

type Period = 'monthly' | 'annual';

const TIERS = [
  {
    name: 'Pay-As-You-Go',
    desc: 'Flexible calls, no commitment',
    monthly: null,
    annual: null,
    amount: '$0.85',
    per: '/call',
    calls: 'Includes 3 min/call · then $0.24/min',
    features: ['24/7 AI call handling', 'Live appointment booking', 'SMS confirmations'],
    cta: 'Get a demo',
    modal: 'demo' as const,
    accent: 'var(--teal)',
    popular: false,
  },
  {
    name: 'Starter',
    desc: 'Single-location shops',
    monthly: 99,
    annual: 82.5,
    amount: null,
    per: '/mo',
    calls: '550 min pool ≈ 220 calls/mo · overage $0.24/min',
    features: ['Everything in Pay-As-You-Go', 'Priority call routing', 'Weekly performance summary'],
    cta: 'Start free trial',
    modal: 'demo' as const,
    checkout: true as const,
    accent: 'var(--magenta)',
    popular: true,
  },
  {
    name: 'Growth',
    desc: 'Higher-volume single locations',
    monthly: 199,
    annual: 165.83,
    amount: null,
    per: '/mo',
    calls: '1,300 min pool ≈ 520 calls/mo · overage $0.22/min',
    features: ['Everything in Starter', 'Custom call-routing rules', 'Dedicated onboarding session'],
    cta: 'Start free trial',
    modal: 'demo' as const,
    checkout: true as const,
    accent: 'var(--violet)',
    popular: false,
  },
  {
    name: 'Multi-Location',
    desc: '3–15 location groups',
    monthly: null,
    annual: null,
    amount: 'Custom',
    per: '',
    calls: 'Volume discount per site',
    features: ['Everything in Growth', 'Cross-location reporting', 'Dedicated account contact'],
    cta: 'Talk to us',
    modal: 'sales' as const,
    accent: 'var(--amber)',
    popular: false,
  },
];

export function Pricing() {
  const [period, setPeriod] = useState<Period>('monthly');
  const [checkoutLoading, setCheckoutLoading] = useState<string | null>(null);
  const { open } = useDemoModal();

  async function handleCheckout(tierName: string) {
    setCheckoutLoading(tierName);
    try {
      const res = await fetch('/api/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier: tierName, period }),
      });
      const data = await res.json();
      if (res.ok && data.url) {
        window.location.href = data.url;
        return;
      }
      // Stripe isn't wired to a real account yet — fall back to the demo
      // form rather than leaving the button dead.
      open('demo');
    } catch {
      open('demo');
    } finally {
      setCheckoutLoading(null);
    }
  }

  return (
    <section id="pricing" className="py-24 md:py-28">
      <Container>
        <Reveal className="max-w-[640px]">
          <div className="eyebrow">Pricing</div>
          <h2 className="mt-4 text-[2rem] font-extrabold tracking-tight text-[var(--ink)] sm:text-[2.5rem]">
            Call capacity that grows with your shop.
          </h2>
          <p className="mt-4 text-[16px] text-[var(--ink-dim)]">
            Pricing covers the AI Receptionist. No setup fee, no long-term contract to start.
          </p>

          <div className="mt-6 inline-flex items-center gap-1 rounded-full border border-[var(--line)] bg-[var(--surface)] p-1">
            {(['monthly', 'annual'] as Period[]).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className="rounded-full px-4 py-2 text-[13px] font-semibold transition-colors"
                style={
                  period === p
                    ? { background: 'var(--ink)', color: 'var(--ground)' }
                    : { color: 'var(--ink-dim)' }
                }
              >
                {p === 'monthly' ? 'Monthly' : 'Annual — 2 months free'}
              </button>
            ))}
          </div>
        </Reveal>

        <div className="mt-12 grid gap-4 lg:grid-cols-4">
          {TIERS.map((t, i) => {
            const price =
              t.amount ?? `$${period === 'annual' && t.annual ? t.annual : t.monthly}`;
            return (
              <Reveal key={t.name} delay={i * 60}>
                <div
                  className="relative flex h-full flex-col rounded-[var(--radius)] border bg-[var(--surface)] p-6"
                  style={{
                    borderColor: t.popular ? t.accent : 'var(--line)',
                    boxShadow: t.popular
                      ? `0 20px 44px -26px color-mix(in oklab, ${t.accent} 60%, transparent)`
                      : undefined,
                  }}
                >
                  {t.popular && (
                    <span
                      className="absolute -top-3 left-6 rounded-full px-3 py-1 font-[family-name:var(--font-data)] text-[10px] font-semibold tracking-[0.08em] text-white uppercase"
                      style={{ background: t.accent }}
                    >
                      Most popular
                    </span>
                  )}
                  <h3 className="text-[17px] font-bold text-[var(--ink)]">{t.name}</h3>
                  <p className="mt-1 text-[12.5px] text-[var(--ink-faint)]">{t.desc}</p>

                  <div className="mt-5 text-[2rem] leading-none font-extrabold text-[var(--ink)]">
                    {price}
                    <span className="text-[13px] font-medium text-[var(--ink-faint)]">
                      {t.per}
                      {t.monthly && period === 'annual' ? ', billed yearly' : ''}
                    </span>
                  </div>
                  <div className="mt-2.5 font-[family-name:var(--font-data)] text-[11.5px] text-[var(--ink-faint)]">
                    {t.calls}
                  </div>

                  <ul className="mt-5 flex-1 space-y-2.5">
                    {t.features.map((f) => (
                      <li key={f} className="flex gap-2 text-[13.5px] text-[var(--ink-dim)]">
                        <span style={{ color: t.accent }}>—</span>
                        {f}
                      </li>
                    ))}
                  </ul>

                  <PillButton
                    href={t.modal ? undefined : '#demo'}
                    onClick={
                      t.checkout ? () => handleCheckout(t.name) : t.modal ? () => open(t.modal) : undefined
                    }
                    disabled={checkoutLoading === t.name}
                    variant={t.popular ? 'primary' : 'outline'}
                    className="mt-6 w-full py-3 text-[13px]"
                  >
                    {checkoutLoading === t.name ? 'Redirecting…' : t.cta}
                  </PillButton>
                </div>
              </Reveal>
            );
          })}
        </div>

        <Reveal delay={120}>
          <div className="mt-8 flex flex-wrap items-start gap-3 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--surface)] p-6">
            <span className="tag">Every plan</span>
            <p className="text-[13.5px] text-[var(--ink-dim)]">
              24/7 AI call handling · calendar/appointment integration · caller &amp; vehicle
              detail capture · full transcripts &amp; call summaries · SMS confirmation ·
              baseline technical/fault-code grounding · 15-day free trial.
            </p>
          </div>
        </Reveal>
      </Container>
    </section>
  );
}

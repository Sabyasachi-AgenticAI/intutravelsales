import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';

// Mirrors the dollar amounts shown in components/pricing.tsx — kept here
// too since a Checkout Session must be priced server-side, never trusting
// amounts a client could tamper with.
const TIER_PRICING = {
  Starter: { monthly: 99, annual: 82.5 },
  Growth: { monthly: 199, annual: 165.83 },
} as const;

type TierName = keyof typeof TIER_PRICING;
type Period = 'monthly' | 'annual';

function isTierName(value: unknown): value is TierName {
  return typeof value === 'string' && value in TIER_PRICING;
}

export async function POST(req: NextRequest) {
  const key = process.env.STRIPE_SECRET_KEY;
  if (!key || key === 'sk_test_placeholder') {
    return NextResponse.json(
      { error: 'Stripe is not configured yet — add a real STRIPE_SECRET_KEY to .env.local.' },
      { status: 501 }
    );
  }

  const { tier, period } = (await req.json()) as { tier?: unknown; period?: unknown };
  if (!isTierName(tier) || (period !== 'monthly' && period !== 'annual')) {
    return NextResponse.json({ error: 'Invalid tier or billing period.' }, { status: 400 });
  }

  const stripe = new Stripe(key);
  const origin = req.nextUrl.origin;
  const monthlyEquivalent = TIER_PRICING[tier][period as Period];
  const unitAmount =
    period === 'annual' ? Math.round(monthlyEquivalent * 12 * 100) : Math.round(monthlyEquivalent * 100);

  const session = await stripe.checkout.sessions.create({
    mode: 'subscription',
    line_items: [
      {
        price_data: {
          currency: 'usd',
          product_data: { name: `intuService — ${tier}` },
          recurring: { interval: period === 'annual' ? 'year' : 'month' },
          unit_amount: unitAmount,
        },
        quantity: 1,
      },
    ],
    success_url: `${origin}/?checkout=success`,
    cancel_url: `${origin}/?checkout=cancelled`,
  });

  return NextResponse.json({ url: session.url });
}

'use client';

import { useSearchParams } from 'next/navigation';

export function CheckoutStatusBanner() {
  const params = useSearchParams();
  const status = params.get('checkout');
  if (status !== 'success' && status !== 'cancelled') return null;

  const isSuccess = status === 'success';
  return (
    <div
      className="border-b px-4 py-3 text-center text-[13.5px]"
      style={{
        borderColor: 'var(--line)',
        background: isSuccess ? 'var(--teal-bg)' : 'var(--coral-bg)',
        color: isSuccess ? 'var(--teal-soft)' : 'var(--coral-soft)',
      }}
    >
      {isSuccess
        ? "You're all set — your trial is starting. We'll be in touch to finish onboarding."
        : 'Checkout was cancelled — no charge was made. Reach out any time if you have questions.'}
    </div>
  );
}

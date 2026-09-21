import { cn } from '@/lib/shadcn/utils';

/**
 * Generic intuService brand backdrop: a lightly-blurred, unbranded garage
 * photo (public/garage-bg-blurred.jpg — free-license Pixabay image) under a
 * flat, even violet-indigo wash — the same treatment as Flowgentic Meet's
 * hero (one consistent tint across the whole photo, not a vignette). Shared
 * by the call screen and the Clerk auth pages.
 */
export function BrandBackdrop({ className }: { className?: string }) {
  return (
    <div
      aria-hidden
      className={cn('pointer-events-none absolute inset-0 bg-[#241b3f]', className)}
      style={{
        backgroundImage: [
          'linear-gradient(180deg, rgba(36,27,63,0.66), rgba(45,32,77,0.6) 50%, rgba(28,20,48,0.72))',
          "url('/garage-bg-blurred.jpg')",
        ].join(', '),
        backgroundSize: 'cover',
        backgroundPosition: 'center',
      }}
    />
  );
}

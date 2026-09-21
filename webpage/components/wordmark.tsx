import { cn } from '@/lib/cn';

// Refined logotype: still the Fredoka wordmark (closest off-the-shelf match
// to Numa's rounded hand-drawn lettermark, see app/layout.tsx), now with a
// two-tone treatment — "intu" solid, "service" in the same violet→magenta
// gradient used on primary buttons and the hero headline — so the mark reads
// as intentional brand color rather than a plain text label.
export function Wordmark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        'font-[family-name:var(--font-logo)] font-semibold tracking-tight whitespace-nowrap',
        className
      )}
    >
      <span className="text-[var(--ink)]">intu</span>
      <span className="bg-gradient-to-r from-[var(--violet-soft)] to-[var(--magenta)] bg-clip-text text-transparent">
        Service
      </span>
    </span>
  );
}

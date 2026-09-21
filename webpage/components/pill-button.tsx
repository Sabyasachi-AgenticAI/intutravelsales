import Link from 'next/link';
import { cn } from '@/lib/cn';

type Variant = 'primary' | 'ghost' | 'outline';

const VARIANT_CLASSES: Record<Variant, string> = {
  primary:
    'bg-gradient-to-r from-[var(--violet)] to-[var(--magenta)] text-white shadow-[0_10px_28px_-8px_rgba(236,72,153,0.55)] hover:shadow-[0_14px_32px_-8px_rgba(236,72,153,0.7)]',
  ghost: 'border border-[var(--line-strong)] text-[var(--ink)] hover:bg-[var(--surface-hover)]',
  outline: 'border border-[var(--line-strong)] text-[var(--ink)] hover:bg-[var(--surface-hover)]',
};

export function PillButton({
  href,
  children,
  variant = 'primary',
  className,
  onClick,
  disabled,
  type = 'button',
}: {
  href?: string;
  children: React.ReactNode;
  variant?: Variant;
  className?: string;
  onClick?: () => void;
  disabled?: boolean;
  type?: 'button' | 'submit';
}) {
  const classes = cn(
    'inline-flex items-center justify-center gap-2 rounded-full px-6 py-3.5 text-sm font-semibold',
    'transition-all duration-150 hover:-translate-y-0.5 disabled:pointer-events-none disabled:opacity-50',
    VARIANT_CLASSES[variant],
    className
  );

  if (href) {
    return (
      <Link href={href} className={classes}>
        {children}
      </Link>
    );
  }

  return (
    <button type={type} onClick={onClick} disabled={disabled} className={classes}>
      {children}
    </button>
  );
}

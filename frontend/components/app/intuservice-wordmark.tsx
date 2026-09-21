import { cn } from '@/lib/shadcn/utils';

interface IntuServiceWordmarkProps {
  className?: string;
}

/**
 * The intuService wordmark: the logo mark, "intu" with a violet tittle (dot)
 * on the dotless i, and "Service" in the same brand violet.
 */
export function IntuServiceWordmark({ className }: IntuServiceWordmarkProps) {
  return (
    <span className={cn('inline-flex items-center gap-2', className)}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/intuservice-logo.svg" alt="intuService logo" className="size-6" />
      <span className="text-lg leading-none font-extrabold tracking-tight">
        {/* dotless i (ı) with a bold, oversized red dot standing in for the tittle */}
        <span className="relative inline-block">
          ı
          <span
            aria-hidden
            className="absolute top-[-0.32em] left-1/2 size-[0.42em] -translate-x-1/2 rounded-full bg-[#7C3AED]"
          />
        </span>
        ntu
        <span className="text-[#7C3AED]">Service</span>
      </span>
    </span>
  );
}

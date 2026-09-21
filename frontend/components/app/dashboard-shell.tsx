'use client';

import { useEffect, useRef, useState } from 'react';
import { useTheme } from 'next-themes';
import { Show, UserButton } from '@clerk/nextjs';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { BrandBackdrop } from '@/components/app/brand-backdrop';
import { IntuServiceWordmark } from '@/components/app/intuservice-wordmark';
import { ThemeToggle } from '@/components/app/theme-toggle';
import { ViewController } from '@/components/app/view-controller';
import { cn } from '@/lib/shadcn/utils';

type Tab = 'call' | 'ops' | 'shop' | 'owner';

const TABS: { id: Tab; label: string }[] = [
  { id: 'call', label: 'Call' },
  { id: 'ops', label: 'Ops' },
  { id: 'shop', label: 'Shop' },
  { id: 'owner', label: 'Owner' },
];

interface DashboardShellProps {
  appConfig: AppConfig;
}

/**
 * Single-surface dashboard that unifies four views:
 *  - Call:  the live voice-agent UI (React).
 *  - Ops:   the district ops dashboard (embedded /ops.html).
 *  - Shop:  the mechanic shop board (embedded /shop.html).
 *  - Owner: coupon editing + active-hours control (embedded /owner.html).
 *
 * All four stay mounted once visited so an in-progress call keeps running
 * while the user browses elsewhere, and the embedded dashboards keep their
 * Supabase realtime subscriptions warm. Agent activity flows agent ->
 * Supabase -> Ops/Shop live.
 */
export function DashboardShell({ appConfig }: DashboardShellProps) {
  const [tab, setTab] = useState<Tab>('call');
  // Track which embedded dashboards have actually been opened, so their iframes
  // (and Supabase realtime subscriptions) only mount on first visit instead of
  // running in the background from page load. Once opened they stay mounted so
  // the live channel isn't dropped when switching tabs.
  const [visited, setVisited] = useState<Record<Tab, boolean>>({
    call: true,
    ops: false,
    shop: false,
    owner: false,
  });
  const { isConnected } = useSessionContext();
  const { resolvedTheme } = useTheme();

  const opsRef = useRef<HTMLIFrameElement>(null);
  const shopRef = useRef<HTMLIFrameElement>(null);
  const ownerRef = useRef<HTMLIFrameElement>(null);

  // Keep the embedded dashboards' theme in lockstep with the app theme,
  // without reloading the iframe (which would drop its realtime channel).
  useEffect(() => {
    const theme = resolvedTheme === 'dark' ? 'dark' : 'light';
    for (const ref of [opsRef, shopRef, ownerRef]) {
      ref.current?.contentWindow?.postMessage({ type: 'intuservice-theme', theme }, '*');
    }
  }, [resolvedTheme, tab]);

  const initialTheme = resolvedTheme === 'dark' ? 'dark' : 'light';

  return (
    <div className="bg-background text-foreground flex h-svh flex-col overflow-hidden">
      <header className="border-border flex shrink-0 flex-wrap items-center gap-x-4 gap-y-2 border-b px-3 py-2.5 sm:px-4 md:px-6">
        <div className="flex min-w-0 shrink-0 items-center gap-2.5">
          <IntuServiceWordmark />
        </div>

        <nav className="flex shrink-0 items-center gap-1" aria-label="Views">
          {TABS.map(({ id, label }) => (
            <button
              key={id}
              type="button"
              onClick={() => {
                setTab(id);
                if (!visited[id]) setVisited((v) => ({ ...v, [id]: true }));
              }}
              aria-current={tab === id ? 'page' : undefined}
              className={cn(
                'rounded-md px-2.5 py-1.5 text-sm font-medium transition-colors sm:px-3',
                tab === id
                  ? 'bg-foreground text-background'
                  : 'text-muted-foreground hover:bg-muted hover:text-foreground'
              )}
            >
              {label}
            </button>
          ))}
        </nav>

        <div className="ml-auto flex shrink-0 items-center gap-2 sm:gap-3">
          {isConnected && (
            <span className="flex items-center gap-1.5 text-xs font-bold tracking-wider text-green-600 dark:text-green-500">
              <span className="inline-block size-2 animate-pulse rounded-full bg-green-500" />
              <span className="hidden sm:inline">LIVE</span>
            </span>
          )}
          <ThemeToggle className="w-auto" />
          <Show when="signed-in">
            <UserButton />
          </Show>
        </div>
      </header>

      <main className="relative flex-1 overflow-hidden">
        {/* Call — always mounted so audio persists across tab switches. The
            `dark` class commits this tab to an immersive dark look, so the
            frosted glass call UI (card, visualizer, text) stays legible over
            the brand gradient regardless of the app-wide theme setting. */}
        <div
          className={cn('dark text-foreground relative h-full w-full', tab !== 'call' && 'hidden')}
        >
          <BrandBackdrop />
          <div className="relative z-10 grid h-full w-full place-content-center">
            <ViewController appConfig={appConfig} />
          </div>
        </div>

        {/* Ops — embedded district dashboard. Mounts on first visit only. */}
        {visited.ops && (
          <iframe
            ref={opsRef}
            title="Ops dashboard"
            src={`/ops.html?theme=${initialTheme}`}
            suppressHydrationWarning
            className={cn('h-full w-full border-0', tab !== 'ops' && 'hidden')}
          />
        )}

        {/* Shop — embedded shop board. Mounts on first visit only. */}
        {visited.shop && (
          <iframe
            ref={shopRef}
            title="Shop board"
            src={`/shop.html?theme=${initialTheme}`}
            suppressHydrationWarning
            className={cn('h-full w-full border-0', tab !== 'shop' && 'hidden')}
          />
        )}

        {/* Owner — coupon editing + active-hours control. Mounts on first visit only. */}
        {visited.owner && (
          <iframe
            ref={ownerRef}
            title="Owner controls"
            src={`/owner.html?theme=${initialTheme}`}
            suppressHydrationWarning
            className={cn('h-full w-full border-0', tab !== 'owner' && 'hidden')}
          />
        )}
      </main>
    </div>
  );
}

'use client';

import { useEffect, useMemo, useState } from 'react';
import { Mic, MicOff, PhoneOff } from 'lucide-react';
import {
  RoomAudioRenderer,
  SessionProvider,
  useAgent,
  useEnsureRoom,
  useLocalParticipant,
  useSession,
  useSessionContext,
  useStartAudio,
} from '@livekit/components-react';
import { getConnectionTokenSource } from '@/lib/token-source';

const STATUS_COPY: Record<string, string> = {
  idle: 'Ready when you are',
  connecting: 'Connecting…',
  'pre-connect-buffering': 'Connecting…',
  initializing: 'Connecting you with Jacqueline…',
  listening: 'Listening',
  thinking: 'Thinking…',
  speaking: 'Speaking',
  failed: "Couldn't connect — try again",
  disconnected: 'Ready when you are',
};

// A different hue per bar so the equalizer feels lively rather than a single
// flat color pulsing up and down.
const EQ_BARS = [
  { h: 26, c: 'var(--violet)' },
  { h: 52, c: 'var(--magenta)' },
  { h: 74, c: 'var(--teal)' },
  { h: 96, c: 'var(--amber)' },
  { h: 64, c: 'var(--coral)' },
  { h: 88, c: 'var(--violet-soft)' },
  { h: 44, c: 'var(--magenta-soft)' },
  { h: 70, c: 'var(--teal-soft)' },
  { h: 34, c: 'var(--amber-soft)' },
  { h: 58, c: 'var(--coral-soft)' },
  { h: 80, c: 'var(--violet)' },
];

/**
 * IMPORTANT: `useSession()` (and the `SessionProvider` tree under it) is only
 * mounted once the visitor explicitly clicks "Start a live call". LiveKit's
 * client begins pre-connect audio buffering — and requests the microphone —
 * as soon as that hook mounts, which would otherwise mean every visitor who
 * merely scrolls past this section on a public marketing page silently
 * dispatches a real, billed agent session. Gating the mount on a click keeps
 * that behind genuine intent, the same trust boundary the main app has via
 * its Welcome screen.
 */
export function VoiceDemo({ agentName }: { agentName: string }) {
  const [started, setStarted] = useState(false);

  if (!started) {
    return <VoiceDemoPoster onStart={() => setStarted(true)} />;
  }

  return <VoiceDemoSession agentName={agentName} />;
}

function VoiceDemoSession({ agentName }: { agentName: string }) {
  const tokenSource = useMemo(() => getConnectionTokenSource(agentName), [agentName]);
  const session = useSession(tokenSource, { agentName });

  return (
    <SessionProvider session={session}>
      <VoiceDemoCard autoStart />
      <RoomAudioRenderer />
    </SessionProvider>
  );
}

function StartAudioFallback() {
  const room = useEnsureRoom();
  const { mergedProps, canPlayAudio } = useStartAudio({ room, props: {} });
  if (canPlayAudio) return null;
  return (
    <button
      {...mergedProps}
      className="mt-3 block w-full text-center text-[12.5px] font-semibold text-[var(--amber-soft)] underline underline-offset-4"
    >
      Tap to enable audio
    </button>
  );
}

function CardShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="w-full max-w-[420px] overflow-hidden rounded-[var(--radius)] border border-[var(--line-strong)] bg-[var(--ground-soft)]/90 shadow-[0_40px_90px_-30px_rgba(0,0,0,0.75)] backdrop-blur-xl">
      {children}
    </div>
  );
}

function CardHeader({ statusLabel, isLive }: { statusLabel: string; isLive: boolean }) {
  return (
    <div className="relative px-7 pt-5 pb-2">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 opacity-40"
        style={{
          background:
            'radial-gradient(70% 70% at 20% 0%, var(--violet-bg), transparent), radial-gradient(70% 70% at 90% 0%, var(--magenta-bg), transparent)',
        }}
      />
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-[13px] bg-gradient-to-br from-[var(--violet)] to-[var(--magenta)] text-[16px] font-bold text-white shadow-[0_6px_18px_-6px_rgba(124,58,237,0.7)]">
            J
          </div>
          <div>
            <div className="text-[15px] font-bold text-[var(--ink)]">Jacqueline</div>
            <div className="font-[family-name:var(--font-data)] text-[10.5px] tracking-[0.05em] text-[var(--ink-faint)] uppercase">
              AI Service Advisor
            </div>
          </div>
        </div>
        <span
          className="inline-flex items-center gap-2 rounded-full border px-3 py-1.5 font-[family-name:var(--font-data)] text-[10.5px] tracking-[0.08em] uppercase"
          style={
            isLive
              ? {
                  color: '#cfe9d8',
                  background: 'rgba(52,211,153,0.12)',
                  borderColor: 'rgba(52,211,153,0.3)',
                }
              : {
                  color: 'var(--ink-dim)',
                  background: 'var(--surface)',
                  borderColor: 'var(--line)',
                }
          }
        >
          {isLive && (
            <span
              className="h-1.5 w-1.5 rounded-full bg-[var(--good)]"
              style={{ animationName: 'pulse-dot', animationDuration: '1.8s', animationTimingFunction: 'ease-in-out', animationIterationCount: 'infinite' }}
            />
          )}
          {statusLabel}
        </span>
      </div>
    </div>
  );
}

function Equalizer({ isLive }: { isLive: boolean }) {
  return (
    <div className="flex h-[92px] items-center justify-center gap-[5px]">
      {EQ_BARS.map((bar, i) => (
        <span
          key={i}
          className="w-[5px] rounded-full"
          style={{
            height: `${bar.h}%`,
            background: bar.c,
            animationName: isLive ? 'eq-bar' : 'none',
            animationDuration: '1.1s',
            animationTimingFunction: 'ease-in-out',
            animationIterationCount: 'infinite',
            animationDelay: `${-i * 0.12}s`,
            opacity: isLive ? 1 : 0.25,
            transform: isLive ? undefined : 'scaleY(0.35)',
            transition: 'opacity 0.3s ease',
          }}
        />
      ))}
    </div>
  );
}

/** The static, pre-click state. No LiveKit session, no mic access — just the visual. */
function VoiceDemoPoster({ onStart }: { onStart: () => void }) {
  return (
    <CardShell>
      <CardHeader statusLabel="Ready when you are" isLive={false} />
      <Equalizer isLive={false} />
      <div className="px-7 pb-7">
        <button
          onClick={onStart}
          className="flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-[var(--violet)] to-[var(--magenta)] py-3.5 text-[14px] font-semibold text-white shadow-[0_10px_28px_-8px_rgba(236,72,153,0.55)] transition-all hover:-translate-y-0.5 hover:shadow-[0_14px_32px_-8px_rgba(236,72,153,0.7)]"
        >
          Start a live call
        </button>
        <p className="mt-4 text-center font-[family-name:var(--font-data)] text-[11px] text-[var(--ink-faint)]">
          Uses your microphone for this call only — nothing is saved beyond the demo.
        </p>
      </div>
    </CardShell>
  );
}

function VoiceDemoCard({ autoStart }: { autoStart?: boolean }) {
  const { isConnected, start, end } = useSessionContext();
  const agent = useAgent();
  const { isMicrophoneEnabled, localParticipant } = useLocalParticipant();
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const active = isConnected && agent.state !== 'failed';
  const statusLabel = active ? (STATUS_COPY[agent.state] ?? 'Connected') : STATUS_COPY.idle;
  const isLive =
    agent.state === 'listening' || agent.state === 'thinking' || agent.state === 'speaking';

  const handleStart = async () => {
    setError(null);
    setStarting(true);
    try {
      await start();
    } catch (e) {
      console.error(e);
      setError("Couldn't start the call — check your mic permissions and try again.");
    } finally {
      setStarting(false);
    }
  };

  // Runs once, right after this component mounts — which only happens after
  // the visitor clicked "Start a live call" on the poster (see VoiceDemo above).
  useEffect(() => {
    if (autoStart) {
      handleStart();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleMic = () => {
    localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled).catch(console.error);
  };

  const handleEnd = async () => {
    await end();
  };

  return (
    <CardShell>
      <CardHeader statusLabel={starting ? 'Connecting…' : statusLabel} isLive={isLive} />
      <Equalizer isLive={isLive} />

      <div className="px-7 pb-7">
        {error && <p className="mb-3 text-center text-[12.5px] text-red-400">{error}</p>}

        {!active ? (
          <button
            onClick={handleStart}
            disabled={starting}
            className="flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-[var(--violet)] to-[var(--magenta)] py-3.5 text-[14px] font-semibold text-white shadow-[0_10px_28px_-8px_rgba(236,72,153,0.55)] transition-all hover:-translate-y-0.5 hover:shadow-[0_14px_32px_-8px_rgba(236,72,153,0.7)] disabled:pointer-events-none disabled:opacity-60"
          >
            {starting ? 'Connecting…' : 'Retry'}
          </button>
        ) : (
          <div className="flex items-center justify-center gap-3">
            <button
              onClick={toggleMic}
              className="flex h-12 w-12 items-center justify-center rounded-full border border-[var(--line-strong)] text-[var(--ink)] transition-colors hover:bg-[var(--surface-hover)]"
              aria-label={isMicrophoneEnabled ? 'Mute microphone' : 'Unmute microphone'}
            >
              {isMicrophoneEnabled ? <Mic size={18} /> : <MicOff size={18} />}
            </button>
            <button
              onClick={handleEnd}
              className="flex h-12 flex-1 items-center justify-center gap-2 rounded-full bg-[var(--coral)] text-[14px] font-semibold text-white transition-colors hover:bg-[#ff8163]"
            >
              <PhoneOff size={16} />
              End call
            </button>
          </div>
        )}

        <StartAudioFallback />

        <p className="mt-4 text-center font-[family-name:var(--font-data)] text-[11px] text-[var(--ink-faint)]">
          Uses your microphone for this call only — nothing is saved beyond the demo.
        </p>
      </div>
    </CardShell>
  );
}

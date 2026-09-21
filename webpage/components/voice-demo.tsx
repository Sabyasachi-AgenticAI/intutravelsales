'use client';

import { useEffect, useMemo, useState } from 'react';
import { Mic, MicOff, PhoneOff, Volume2, VolumeX } from 'lucide-react';
import {
  RoomAudioRenderer,
  SessionProvider,
  useAgent,
  useEnsureRoom,
  useLocalParticipant,
  useRoomContext,
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
 * mounted once the visitor explicitly clicks "Start a live call" AND agrees to
 * the recording-consent notice below. LiveKit's client begins pre-connect
 * audio buffering — and requests the microphone — as soon as that hook
 * mounts, which would otherwise mean every visitor who merely scrolls past
 * this section on a public marketing page silently dispatches a real, billed
 * agent session. Gating the mount on explicit consent keeps that behind
 * genuine, informed intent, the same trust boundary the main app has via its
 * Welcome screen.
 */
export function VoiceDemo({ agentName }: { agentName: string }) {
  const [started, setStarted] = useState(false);
  const [consentOpen, setConsentOpen] = useState(false);

  if (started) {
    return <VoiceDemoSession agentName={agentName} />;
  }

  return (
    <>
      <VoiceDemoPoster onStart={() => setConsentOpen(true)} />
      {consentOpen && (
        <ConsentModal
          onAgree={() => {
            setConsentOpen(false);
            setStarted(true);
          }}
          onCancel={() => setConsentOpen(false)}
        />
      )}
    </>
  );
}

function ConsentModal({ onAgree, onCancel }: { onAgree: () => void; onCancel: () => void }) {
  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 px-4 py-10 backdrop-blur-sm"
      onClick={onCancel}
    >
      <div
        className="w-full max-w-[440px] rounded-[var(--radius)] border border-[var(--line-strong)] bg-[var(--ground-soft)] p-7 shadow-[0_30px_80px_-20px_rgba(0,0,0,0.6)]"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="eyebrow">Terms and conditions</div>
        <p className="mt-4 text-[13.5px] leading-relaxed text-[var(--ink-dim)]">
          By clicking &quot;Agree,&quot; and each time I interact with this AI agent, I consent
          to the recording, storage, and sharing of my communications with third-party service
          providers, and as described in the Privacy Policy. If you do not wish to have your
          conversations recorded, please refrain from using this service.
        </p>
        <div className="mt-6 flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 rounded-full border border-[var(--line-strong)] py-3 text-[13.5px] font-semibold text-[var(--ink)] transition-colors hover:bg-[var(--surface-hover)]"
          >
            Cancel
          </button>
          <button
            onClick={onAgree}
            className="flex-1 rounded-full bg-gradient-to-r from-[var(--violet)] to-[var(--magenta)] py-3 text-[13.5px] font-semibold text-white shadow-[0_10px_28px_-8px_rgba(236,72,153,0.55)] transition-all hover:-translate-y-0.5"
          >
            Agree
          </button>
        </div>
      </div>
    </div>
  );
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
    <div className="relative w-full max-w-[400px] overflow-hidden rounded-[var(--radius)] border border-[var(--line-strong)] bg-[var(--ground-soft)]/90 px-8 pt-8 pb-7 text-center shadow-[0_40px_90px_-30px_rgba(0,0,0,0.75)] backdrop-blur-xl">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            'radial-gradient(60% 50% at 50% 0%, var(--violet-bg), transparent), radial-gradient(50% 40% at 100% 100%, var(--magenta-bg), transparent)',
        }}
      />
      {children}
    </div>
  );
}

function StatusPill({ statusLabel, isLive }: { statusLabel: string; isLive: boolean }) {
  return (
    <span
      className="absolute top-5 right-5 inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-[family-name:var(--font-data)] text-[9.5px] tracking-[0.06em] uppercase"
      style={
        isLive
          ? { color: '#cfe9d8', background: 'rgba(52,211,153,0.12)', borderColor: 'rgba(52,211,153,0.3)' }
          : { color: 'var(--ink-dim)', background: 'var(--surface)', borderColor: 'var(--line)' }
      }
    >
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{
          background: isLive ? 'var(--good)' : 'var(--ink-faint)',
          animationName: isLive ? 'pulse-dot' : 'none',
          animationDuration: '1.8s',
          animationTimingFunction: 'ease-in-out',
          animationIterationCount: 'infinite',
        }}
      />
      {statusLabel}
    </span>
  );
}

// A centered "voice orb" — a dashed ring slowly rotating around a soft glass
// circle, with a compact waveform inside — reads as a single focal object
// instead of a name row and a separate visualizer panel stacked on top of
// each other. Inspired by autoleap.com/air's receptionist widget, restyled
// in our own dark, multi-hue palette rather than copied wholesale.
function VoiceOrb({ isLive }: { isLive: boolean }) {
  return (
    <div className="relative mx-auto flex h-[128px] w-[128px] items-center justify-center">
      <div
        className="absolute inset-0 rounded-full border-2 border-dashed"
        style={{ borderColor: 'var(--violet-soft)', opacity: 0.5, animation: 'spin 14s linear infinite' }}
      />
      <div
        aria-hidden
        className="absolute inset-3 rounded-full blur-lg"
        style={{ background: 'radial-gradient(circle, var(--violet-bg), transparent 70%)' }}
      />
      <div className="relative flex h-[96px] w-[96px] items-center justify-center rounded-full border border-[var(--line-strong)] bg-gradient-to-br from-[var(--violet-bg)] to-[var(--magenta-bg)]">
        <div className="flex h-[30px] items-end justify-center gap-[3px]">
          {EQ_BARS.slice(0, 7).map((bar, i) => (
            <span
              key={i}
              className="w-[3.5px] rounded-full"
              style={{
                height: `${bar.h}%`,
                background: bar.c,
                animationName: isLive ? 'eq-bar' : 'none',
                animationDuration: '1.1s',
                animationTimingFunction: 'ease-in-out',
                animationIterationCount: 'infinite',
                animationDelay: `${-i * 0.12}s`,
                opacity: isLive ? 1 : 0.35,
                transform: isLive ? undefined : 'scaleY(0.4)',
                transition: 'opacity 0.3s ease',
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function VoiceCardBody({ statusLabel, isLive }: { statusLabel: string; isLive: boolean }) {
  return (
    <>
      <StatusPill statusLabel={statusLabel} isLive={isLive} />
      <VoiceOrb isLive={isLive} />
      <div className="mt-5 text-[18px] font-bold text-[var(--ink)]">Jacqueline</div>
      <div className="mt-0.5 font-[family-name:var(--font-data)] text-[10.5px] tracking-[0.06em] text-[var(--ink-faint)] uppercase">
        AI Service Advisor
      </div>
    </>
  );
}

// Counts up from 00:00 as soon as the call becomes active, and resets
// whenever it isn't — mirrors a phone app's in-call duration readout.
function CallTimer({ active }: { active: boolean }) {
  const [elapsedS, setElapsedS] = useState(0);

  useEffect(() => {
    if (!active) {
      setElapsedS(0);
      return;
    }
    const startedAt = Date.now();
    setElapsedS(0);
    const id = setInterval(() => {
      setElapsedS(Math.floor((Date.now() - startedAt) / 1000));
    }, 1000);
    return () => clearInterval(id);
  }, [active]);

  const mm = String(Math.floor(elapsedS / 60)).padStart(2, '0');
  const ss = String(elapsedS % 60).padStart(2, '0');

  return (
    <div className="font-[family-name:var(--font-data)] text-[13px] tracking-[0.05em] text-[var(--ink-dim)]">
      {mm}:{ss}
    </div>
  );
}

// Pill-shaped in-call control bar — mic mute, speaker mute, and end call —
// inspired by the reference call-widget's layout, in our own dark palette.
function CallControlBar({
  isMicrophoneEnabled,
  onToggleMic,
  isSpeakerEnabled,
  onToggleSpeaker,
  onEnd,
}: {
  isMicrophoneEnabled: boolean;
  onToggleMic: () => void;
  isSpeakerEnabled: boolean;
  onToggleSpeaker: () => void;
  onEnd: () => void;
}) {
  return (
    <div className="mt-3 flex items-center justify-center gap-1.5 rounded-full border border-[var(--line-strong)] bg-[var(--surface)] p-1.5">
      <button
        onClick={onToggleMic}
        aria-label={isMicrophoneEnabled ? 'Mute microphone' : 'Unmute microphone'}
        className="flex h-11 w-11 items-center justify-center rounded-full text-[var(--ink)] transition-colors hover:bg-[var(--surface-hover)]"
      >
        {isMicrophoneEnabled ? <Mic size={18} /> : <MicOff size={18} />}
      </button>
      <button
        onClick={onToggleSpeaker}
        aria-label={isSpeakerEnabled ? 'Mute speaker' : 'Unmute speaker'}
        className="flex h-11 w-11 items-center justify-center rounded-full text-[var(--ink)] transition-colors hover:bg-[var(--surface-hover)]"
      >
        {isSpeakerEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
      </button>
      <button
        onClick={onEnd}
        aria-label="End call"
        className="flex h-11 w-11 items-center justify-center rounded-full bg-[var(--coral)] text-white transition-colors hover:bg-[#ff8163]"
      >
        <PhoneOff size={18} />
      </button>
    </div>
  );
}

/** The static, pre-click state. No LiveKit session, no mic access — just the visual. */
function VoiceDemoPoster({ onStart }: { onStart: () => void }) {
  return (
    <CardShell>
      <VoiceCardBody statusLabel="Available" isLive={false} />
      <div className="mt-6">
        <button
          onClick={onStart}
          className="flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-[var(--violet)] to-[var(--magenta)] py-3.5 text-[14.5px] font-semibold text-white shadow-[0_10px_28px_-8px_rgba(236,72,153,0.55)] transition-all hover:-translate-y-0.5 hover:shadow-[0_14px_32px_-8px_rgba(236,72,153,0.7)]"
        >
          Start a live call
        </button>
        <p className="mt-3.5 text-center text-[12.5px] text-[var(--ink-faint)]">
          Tap to talk — Jacqueline picks up instantly.
        </p>
      </div>
    </CardShell>
  );
}

function VoiceDemoCard({ autoStart }: { autoStart?: boolean }) {
  const { isConnected, start, end } = useSessionContext();
  const agent = useAgent();
  const { isMicrophoneEnabled, localParticipant } = useLocalParticipant();
  const room = useRoomContext();
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSpeakerEnabled, setIsSpeakerEnabled] = useState(true);

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

  const toggleSpeaker = () => {
    const next = !isSpeakerEnabled;
    setIsSpeakerEnabled(next);
    room.remoteParticipants.forEach((participant) => {
      participant.setVolume(next ? 1 : 0);
    });
  };

  const handleEnd = async () => {
    await end();
  };

  return (
    <CardShell>
      <VoiceCardBody statusLabel={starting ? 'Connecting…' : statusLabel} isLive={isLive} />

      <div className="mt-6">
        {error && <p className="mb-3 text-center text-[12.5px] text-red-400">{error}</p>}

        {!active ? (
          <button
            onClick={handleStart}
            disabled={starting}
            className="flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-[var(--violet)] to-[var(--magenta)] py-3.5 text-[14.5px] font-semibold text-white shadow-[0_10px_28px_-8px_rgba(236,72,153,0.55)] transition-all hover:-translate-y-0.5 hover:shadow-[0_14px_32px_-8px_rgba(236,72,153,0.7)] disabled:pointer-events-none disabled:opacity-60"
          >
            {starting ? 'Connecting…' : 'Retry'}
          </button>
        ) : (
          <div className="flex flex-col items-center">
            <CallTimer active={active} />
            <CallControlBar
              isMicrophoneEnabled={isMicrophoneEnabled}
              onToggleMic={toggleMic}
              isSpeakerEnabled={isSpeakerEnabled}
              onToggleSpeaker={toggleSpeaker}
              onEnd={handleEnd}
            />
          </div>
        )}

        <StartAudioFallback />
      </div>
    </CardShell>
  );
}

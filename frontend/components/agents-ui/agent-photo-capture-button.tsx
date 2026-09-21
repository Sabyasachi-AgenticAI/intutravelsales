'use client';

import { useRef, useState } from 'react';
import { CameraIcon, LoaderIcon } from 'lucide-react';
import { useRoomContext } from '@livekit/components-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/shadcn/utils';

/**
 * Byte-stream topic the photo is sent on. Must match `PHOTO_TOPIC` in
 * `my-agent/src/agent.py`, which registers the corresponding
 * `register_byte_stream_handler` to receive it.
 */
export const PHOTO_TOPIC = 'pepboys.photo';

export interface AgentPhotoCaptureButtonProps {
  /**
   * The visual style of the button, matching the surrounding control bar.
   *
   * @default 'default'
   */
  variant?: 'default' | 'outline' | 'livekit';
  className?: string;
  /** Called if sending the captured photo to the agent fails. */
  onError?: (error: Error) => void;
  /** Called with the photo file right after it's successfully sent to the agent. */
  onPhotoSent?: (file: File) => void;
}

/**
 * A momentary action button that lets the caller take or upload a photo of
 * their vehicle mid-call, sending it to the agent for analysis. Uses a
 * native file input (rather than grabbing a frame from an already-published
 * camera track) so it works with or without an active camera track, and
 * gives a native "take photo" experience on mobile via `capture="environment"`.
 */
export function AgentPhotoCaptureButton({
  variant = 'default',
  className,
  onError,
  onPhotoSent,
}: AgentPhotoCaptureButtonProps) {
  const room = useRoomContext();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isSending, setIsSending] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    // Reset so selecting the same file again still fires onChange.
    e.target.value = '';
    if (!file) return;

    try {
      setIsSending(true);
      await room.localParticipant.sendFile(file, {
        mimeType: file.type,
        topic: PHOTO_TOPIC,
      });
      onPhotoSent?.(file);
    } catch (error) {
      onError?.(error as Error);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <>
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={handleFileChange}
      />
      <Button
        type="button"
        size="icon"
        variant={variant === 'outline' ? 'outline' : 'default'}
        aria-label="Take a photo"
        title="Take a photo"
        disabled={isSending}
        onClick={() => inputRef.current?.click()}
        className={cn(
          // This is a momentary action, not a persistent on/off toggle, so it
          // always uses the pill controls' idle appearance rather than the
          // on/off `data-state` styling the Toggle-based controls rely on.
          variant === 'livekit' && 'bg-accent hover:bg-foreground/10 rounded-full',
          className
        )}
      >
        {isSending ? <LoaderIcon className="animate-spin" /> : <CameraIcon />}
      </Button>
    </>
  );
}

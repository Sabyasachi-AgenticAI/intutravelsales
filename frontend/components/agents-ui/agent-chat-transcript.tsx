'use client';

import { type ComponentProps } from 'react';
import { AnimatePresence } from 'motion/react';
import { type AgentState, type ReceivedMessage } from '@livekit/components-react';
import { AgentChatIndicator } from '@/components/agents-ui/agent-chat-indicator';
import {
  Conversation,
  ConversationContent,
  ConversationScrollButton,
} from '@/components/ai-elements/conversation';
import {
  Message,
  MessageAttachment,
  MessageAttachments,
  MessageContent,
  MessageResponse,
} from '@/components/ai-elements/message';

/**
 * A photo the caller sent mid-call via the in-call capture button. Rendered
 * as its own chat bubble, merged chronologically with text messages — the
 * agent's byte-stream photo upload has no representation in the LiveKit chat
 * transcript on its own, so the session view supplies these locally.
 */
export interface PhotoAttachmentItem {
  id: string;
  timestamp: number;
  url: string;
  filename?: string;
}

/**
 * Props for the AgentChatTranscript component.
 */
export interface AgentChatTranscriptProps extends ComponentProps<'div'> {
  /**
   * The current state of the agent. When 'thinking', displays a loading indicator.
   */
  agentState?: AgentState;
  /**
   * Array of messages to display in the transcript.
   * @defaultValue []
   */
  messages?: ReceivedMessage[];
  /**
   * Photos the caller sent mid-call, rendered as their own bubbles merged
   * chronologically with `messages`.
   * @defaultValue []
   */
  photos?: PhotoAttachmentItem[];
  /**
   * Additional CSS class names to apply to the conversation container.
   */
  className?: string;
}

/**
 * A chat transcript component that displays a conversation between the user and agent.
 * Shows messages with timestamps and origin indicators, plus a thinking indicator
 * when the agent is processing.
 *
 * @extends ComponentProps<'div'>
 *
 * @example
 * ```tsx
 * <AgentChatTranscript
 *   agentState={agentState}
 *   messages={chatMessages}
 * />
 * ```
 */
type TranscriptItem =
  | { kind: 'message'; timestamp: number; data: ReceivedMessage }
  | { kind: 'photo'; timestamp: number; data: PhotoAttachmentItem };

export function AgentChatTranscript({
  agentState,
  messages = [],
  photos = [],
  className,
  ...props
}: AgentChatTranscriptProps) {
  const locale = navigator?.language ?? 'en-US';
  const items: TranscriptItem[] = [
    ...messages.map((m) => ({ kind: 'message' as const, timestamp: m.timestamp, data: m })),
    ...photos.map((p) => ({ kind: 'photo' as const, timestamp: p.timestamp, data: p })),
  ].sort((a, b) => a.timestamp - b.timestamp);

  return (
    <Conversation className={className} {...props}>
      <ConversationContent>
        {items.map((item) => {
          const time = new Date(item.timestamp);
          const title = time.toLocaleTimeString(locale, { timeStyle: 'full' });

          if (item.kind === 'photo') {
            const { id, url, filename } = item.data;
            return (
              <Message key={id} title={title} from="user">
                <MessageAttachments>
                  <MessageAttachment
                    data={{ type: 'file', mediaType: 'image/jpeg', url, filename }}
                  />
                </MessageAttachments>
              </Message>
            );
          }

          const { id, from, message } = item.data;
          const messageOrigin = from?.isLocal ? 'user' : 'assistant';

          return (
            <Message key={id} title={title} from={messageOrigin}>
              <MessageContent>
                <MessageResponse>{message}</MessageResponse>
              </MessageContent>
            </Message>
          );
        })}
        <AnimatePresence>
          {agentState === 'thinking' && <AgentChatIndicator size="sm" />}
        </AnimatePresence>
      </ConversationContent>
      <ConversationScrollButton />
    </Conversation>
  );
}

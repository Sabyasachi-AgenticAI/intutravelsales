import { useEffect } from 'react';
import { toast as sonnerToast } from 'sonner';
import { useAgent, useSessionContext, useSessionMessages } from '@livekit/components-react';

export function useAgentErrors() {
  const session = useSessionContext();
  const agent = useAgent();
  const { messages } = useSessionMessages(session);
  const { isConnected, end } = session;

  useEffect(() => {
    if (!isConnected || agent.state !== 'failed') {
      return;
    }

    // LiveKit reports ANY agent departure as a `failed` state — including the
    // normal case where our agent ends the call itself (the `end_call` tool).
    // If a conversation actually happened, the call simply finished; only treat
    // it as an interruption when no messages were ever exchanged (the agent
    // genuinely failed to join / dropped before talking). No dev-facing guide
    // link either way — this is caller-facing.
    const callHappened = messages.length > 0;

    if (callHappened) {
      sonnerToast('The call has ended.');
    } else {
      sonnerToast('The call was unexpectedly interrupted.');
    }

    end();
  }, [agent, isConnected, end, messages]);
}

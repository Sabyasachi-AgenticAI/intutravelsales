import { TokenSource } from 'livekit-client';

/**
 * Builds a token source that calls our own `/api/token` route and asks it to
 * dispatch the named agent into the room (see app/api/token/route.ts).
 */
export function getConnectionTokenSource(agentName: string) {
  return TokenSource.custom(async () => {
    const roomConfig = { agents: [{ agent_name: agentName }] };

    const res = await fetch('/api/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ room_config: roomConfig }),
    });

    if (!res.ok) {
      throw new Error(`Failed to fetch connection details (${res.status})`);
    }

    return res.json();
  });
}

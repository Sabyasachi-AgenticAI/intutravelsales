export interface AppConfig {
  pageTitle: string;
  pageDescription: string;
  companyName: string;

  supportsChatInput: boolean;
  supportsVideoInput: boolean;
  supportsScreenShare: boolean;
  supportsPhotoCapture: boolean;
  isPreConnectBufferEnabled: boolean;

  logo: string;
  startButtonText: string;
  accent?: string;
  logoDark?: string;
  accentDark?: string;

  audioVisualizerType?: 'bar' | 'wave' | 'grid' | 'radial' | 'aura';
  audioVisualizerColor?: `#${string}`;
  audioVisualizerColorDark?: `#${string}`;
  audioVisualizerColorShift?: number;
  audioVisualizerBarCount?: number;
  audioVisualizerGridRowCount?: number;
  audioVisualizerGridColumnCount?: number;
  audioVisualizerRadialBarCount?: number;
  audioVisualizerRadialRadius?: number;
  audioVisualizerWaveLineWidth?: number;

  // agent dispatch configuration
  agentName?: string;

  // LiveKit Cloud Sandbox configuration
  sandboxId?: string;
}

export const APP_CONFIG_DEFAULTS: AppConfig = {
  companyName: 'intuService',
  pageTitle: 'intuService — AI Voice Service Advisor',
  pageDescription:
    'The AI Service Advisor that answers every call, triages the problem, and books the bay — powered by intuService.',

  supportsChatInput: true,
  // Live camera/screen-share vision (describe_visual, Gemini) is parked as a
  // dummy capability until a Gemini Live API key is provided — hide the
  // controls so callers aren't offered a feature that won't do anything.
  // Photo upload (Qwen VLM) is the only active vision path for now.
  supportsVideoInput: false,
  supportsScreenShare: false,
  supportsPhotoCapture: true,
  isPreConnectBufferEnabled: true,

  logo: '/intuservice-logo.svg',
  accent: '#7C3AED',
  logoDark: '/intuservice-logo.svg',
  accentDark: '#A78BFA',
  startButtonText: 'Start call',

  // audio visualization configuration.
  // 'bar' is a lightweight canvas visualizer; the 'aura' option is a full WebGL
  // shader that runs a continuous GPU render loop and makes the UI feel sluggish.
  audioVisualizerType: 'bar',
  audioVisualizerColor: '#7C3AED',
  audioVisualizerColorDark: '#A78BFA',

  // agent dispatch configuration
  agentName: process.env.AGENT_NAME ?? undefined,

  // LiveKit Cloud Sandbox configuration
  sandboxId: undefined,
};

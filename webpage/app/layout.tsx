import type { Metadata } from 'next';
import { Fredoka, IBM_Plex_Mono, Plus_Jakarta_Sans, Sora } from 'next/font/google';
import './globals.css';

const display = Plus_Jakarta_Sans({
  variable: '--font-display',
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
});

const mono = IBM_Plex_Mono({
  variable: '--font-mono',
  subsets: ['latin'],
  weight: ['400', '500', '600'],
});

// A clean modern grotesque reserved for the nav tagline — a deliberately
// different feel from the mono "data" font used elsewhere.
const tagline = Sora({
  variable: '--font-tagline',
  subsets: ['latin'],
  weight: ['500', '600'],
});

// Numa's own "numa" logo turns out to be a custom hand-drawn vector
// lettermark, not text in any font — so there's no font that reproduces it
// exactly (and we shouldn't trace their artwork). Fredoka is the closest
// off-the-shelf match to that soft, rounded, lowercase feel; used only for
// the wordmark (see nav.tsx / footer.tsx), not the rest of the site's type.
const wordmark = Fredoka({
  variable: '--font-wordmark',
  subsets: ['latin'],
  weight: ['500', '600', '700'],
});

export const metadata: Metadata = {
  title: 'intuService — The AI Service Advisor for Auto Repair Shops',
  description:
    'intuService answers every call, triages the problem, and books the bay — day or night. Talk to it live, see what it costs, and see what it does for a shop that never wants a call to go to voicemail again.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${display.variable} ${mono.variable} ${wordmark.variable} ${tagline.variable}`}
    >
      <body>{children}</body>
    </html>
  );
}

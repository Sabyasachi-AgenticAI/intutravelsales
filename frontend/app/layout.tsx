import { Poppins, Public_Sans } from 'next/font/google';
import localFont from 'next/font/local';
import { headers } from 'next/headers';
import { ClerkProvider } from '@clerk/nextjs';
import { ThemeProvider } from '@/components/app/theme-provider';
import { cn } from '@/lib/shadcn/utils';
import { getAppConfig, getStyles } from '@/lib/utils';
import '@/styles/globals.css';

const publicSans = Public_Sans({
  variable: '--font-public-sans',
  subsets: ['latin'],
});

// Bold, rounded display face for the hero headline/CTA (see welcome-view.tsx)
// — closer to the chunky, friendly type Flowgentic Meet's landing uses than
// Public Sans reads at large display sizes.
const poppins = Poppins({
  variable: '--font-poppins',
  weight: ['800', '900'],
  subsets: ['latin'],
});

const commitMono = localFont({
  display: 'swap',
  variable: '--font-commit-mono',
  src: [
    {
      path: '../fonts/CommitMono-400-Regular.otf',
      weight: '400',
      style: 'normal',
    },
    {
      path: '../fonts/CommitMono-700-Regular.otf',
      weight: '700',
      style: 'normal',
    },
    {
      path: '../fonts/CommitMono-400-Italic.otf',
      weight: '400',
      style: 'italic',
    },
    {
      path: '../fonts/CommitMono-700-Italic.otf',
      weight: '700',
      style: 'italic',
    },
  ],
});

interface RootLayoutProps {
  children: React.ReactNode;
}

export default async function RootLayout({ children }: RootLayoutProps) {
  const hdrs = await headers();
  const appConfig = await getAppConfig(hdrs);
  const styles = getStyles(appConfig);
  const { pageTitle, pageDescription } = appConfig;

  return (
    <ClerkProvider>
      <html
        lang="en"
        suppressHydrationWarning
        className={cn(
          publicSans.variable,
          commitMono.variable,
          poppins.variable,
          'scroll-smooth font-sans antialiased'
        )}
      >
        <head>
          {styles && <style>{styles}</style>}
          <title>{pageTitle}</title>
          <meta name="description" content={pageDescription} />
        </head>
        <body className="overflow-x-hidden">
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            {/* The unified dashboard shell (components/app/dashboard-shell.tsx)
                owns the top nav and theme toggle now, so the standalone header
                and floating toggle that shipped with the starter are gone. */}
            {children}
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}

import { Suspense } from 'react';
import { Capabilities } from '@/components/capabilities';
import { CheckoutStatusBanner } from '@/components/checkout-status-banner';
import { DemoModalProvider } from '@/components/demo-modal';
import { FAQ } from '@/components/faq';
import { FinalCTA } from '@/components/final-cta';
import { Footer } from '@/components/footer';
import { Hero } from '@/components/hero';
import { HowItWorks } from '@/components/how-it-works';
import { LiveDemo } from '@/components/live-demo';
import { Nav } from '@/components/nav';
import { Pricing } from '@/components/pricing';
import { Roadmap } from '@/components/roadmap';
import { ScheduleShowcase } from '@/components/schedule-showcase';
import { StatsBand } from '@/components/stats-band';

export default function Home() {
  const agentName = process.env.AGENT_NAME || 'my-agent';

  return (
    <DemoModalProvider>
      <Suspense fallback={null}>
        <CheckoutStatusBanner />
      </Suspense>
      <Nav />
      <Hero />
      <StatsBand />
      <Capabilities />
      <HowItWorks />
      <ScheduleShowcase />
      <LiveDemo agentName={agentName} />
      <Roadmap />
      <Pricing />
      <FAQ />
      <FinalCTA />
      <Footer />
    </DemoModalProvider>
  );
}

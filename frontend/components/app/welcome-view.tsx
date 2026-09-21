'use client';

import { ArrowRightIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface WelcomeViewProps {
  startButtonText: string;
  onStartCall: () => void;
}

export const WelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & WelcomeViewProps) => {
  return (
    <div ref={ref}>
      <section className="relative flex flex-col items-center justify-center px-6 text-center">
        <h1 className="max-w-lg font-[family-name:var(--font-poppins)] text-4xl leading-[1.15] font-extrabold tracking-tight text-white sm:text-5xl">
          intuService
          <br />
          <span className="bg-gradient-to-r from-[#A78BFA] to-[#7C3AED] bg-clip-text text-transparent">
            AI Voice Agent
          </span>
        </h1>
        <p className="mt-5 max-w-md text-base leading-6 text-white/60">
          Every call answered instantly — symptoms triaged, parts checked, and the appointment
          booked, all in one natural conversation.
        </p>

        <Button
          size="lg"
          onClick={onStartCall}
          className="mt-8 h-12 rounded-full bg-gradient-to-r from-[#7C3AED] to-[#6D28D9] px-8 font-[family-name:var(--font-poppins)] text-sm font-extrabold text-white shadow-lg shadow-[#7C3AED]/30 hover:from-[#8B5CF6] hover:to-[#7C3AED]"
        >
          {startButtonText}
          <ArrowRightIcon className="size-4" />
        </Button>

        <p className="mt-6 font-mono text-[11px] tracking-wider text-white/40 uppercase">
          Powered by Flowgentic AI Framework
        </p>
      </section>
    </div>
  );
};

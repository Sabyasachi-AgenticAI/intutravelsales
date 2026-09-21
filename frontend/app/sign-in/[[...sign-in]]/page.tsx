import { SignIn } from '@clerk/nextjs';
import { BrandBackdrop } from '@/components/app/brand-backdrop';

export default function SignInPage() {
  return (
    <div className="dark relative grid min-h-svh w-full place-items-center p-6">
      <BrandBackdrop />
      <div className="relative z-10">
        <SignIn />
      </div>
    </div>
  );
}

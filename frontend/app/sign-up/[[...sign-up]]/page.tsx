import { SignUp } from '@clerk/nextjs';
import { BrandBackdrop } from '@/components/app/brand-backdrop';

export default function SignUpPage() {
  return (
    <div className="dark relative grid min-h-svh w-full place-items-center p-6">
      <BrandBackdrop />
      <div className="relative z-10">
        <SignUp />
      </div>
    </div>
  );
}

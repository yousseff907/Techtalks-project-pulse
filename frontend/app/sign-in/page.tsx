import Link from "next/link";
import { AuthCard } from "@/components/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function SignInPage() {
  return (
    <AuthCard
      title="Sign in to Project Pulse"
      description="Enter your email — we'll send you a verification code. No password required."
      footer={
        <>
          Don't have an account?{" "}
          <Link href="/sign-up" className="font-medium text-primary underline-offset-4 hover:underline">
            Sign up
          </Link>
        </>
      }
    >
      {/* Static markup only — auth logic comes in a future task */}
      <div className="space-y-2">
        <Label htmlFor="email">Email address</Label>
        <Input id="email" name="email" type="email" placeholder="you@company.com" />
      </div>
      <Button className="w-full">Send verification code</Button>
    </AuthCard>
  );
}
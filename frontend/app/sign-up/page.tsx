import Link from "next/link";
import { AuthCard } from "@/components/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function SignUpPage() {
  return (
    <AuthCard
      title="Create your account"
      description="Start aggregating your team's work in minutes. We'll email you a verification code."
      footer={
        <>
          Already have an account?{" "}
          <Link href="/sign-in" className="font-medium text-primary underline-offset-4 hover:underline">
            Sign in
          </Link>
        </>
      }
    >
      {/* Static markup only — auth logic comes in a future task */}
      <div className="space-y-2">
        <Label htmlFor="name">Full name</Label>
        <Input id="name" name="name" placeholder="Alex Morgan" />
      </div>
      <div className="space-y-2">
        <Label htmlFor="workspace">Workspace name</Label>
        <Input id="workspace" name="workspace" placeholder="Team Alpha" />
      </div>
      <div className="space-y-2">
        <Label htmlFor="email">Email address</Label>
        <Input id="email" name="email" type="email" placeholder="you@company.com" />
      </div>
      <Button className="w-full">Create account</Button>
    </AuthCard>
  );
}
import Link from "next/link";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";

export default function LandingPage() {
  return (
    <div className="flex min-h-svh flex-col">
      <SiteHeader />

      <main className="flex flex-1 items-center">
        <section className="mx-auto w-full max-w-3xl px-6 py-24 text-center">
          <p className="mb-4 text-sm font-medium text-muted-foreground">
            Unified project management
          </p>
          <h1 className="text-balance text-4xl font-semibold tracking-tight sm:text-5xl">
            Every task from Jira and Notion, in one pulse.
          </h1>
          <p className="mx-auto mt-4 max-w-xl text-balance text-muted-foreground">
            Project Pulse aggregates your team's work across tools so you
            always know what's moving — and what's stuck.
          </p>

          <div className="mt-8 flex items-center justify-center gap-3">
            <Button asChild size="lg">
              <Link href="/sign-up">Get started</Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <Link href="/sign-in">Sign in</Link>
            </Button>
          </div>
        </section>
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto max-w-6xl px-6 py-6 text-sm text-muted-foreground">
          © {new Date().getFullYear()} Project Pulse
        </div>
      </footer>
    </div>
  );
}
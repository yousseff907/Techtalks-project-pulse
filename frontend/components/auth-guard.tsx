"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";

function AuthGuardFallback() {
	return (
		<div className="flex min-h-svh items-center justify-center">
			<div
				className="size-6 animate-spin rounded-full border-2 border-muted border-t-foreground"
				role="status"
				aria-label="Loading"
			/>
		</div>
	);
}

export function AuthGuard({ children }: { children: React.ReactNode }) {
	const router = useRouter();
	const accessToken = useAuthStore((state) => state.accessToken);
	const hasHydrated = useAuthStore((state) => state.hasHydrated);

	useEffect(() => {
		// Wait for the persisted store to load from localStorage before deciding,
		// otherwise a logged-in user would be bounced on every refresh.
		if (!hasHydrated) return;
		if (!accessToken) {
			router.replace("/sign-in");
		}
	}, [hasHydrated, accessToken, router]);

	// Render the fallback (never the protected children) until we know the user
	// is authenticated, so protected content can't flash before a redirect.
	if (!hasHydrated || !accessToken) {
		return <AuthGuardFallback />;
	}

	return <>{children}</>;
}

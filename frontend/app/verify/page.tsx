"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AuthCard } from "@/components/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/lib/auth-store";

const verifySchema = z.object({
	code: z
		.string()
		.length(6, "Code must be 6 digits")
		.regex(/^\d+$/, "Code must contain only numbers"),
});

type VerifyFormData = z.infer<typeof verifySchema>;

interface VerifyResponse {
	access_token: string;
	token_type: string;
}

async function verifyRequest(payload: { email: string; code: string }): Promise<VerifyResponse> {
	const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/verify`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail);
	}

	return response.json();
}

async function resendCodeRequest(email: string) {
	const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ email }),
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail);
	}

	return response.json();
}

function VerifyPageContent() {
	const router = useRouter();
	const searchParams = useSearchParams();
	const email = searchParams.get("email") ?? "";
	const setAccessToken = useAuthStore((state) => state.setAccessToken);

	const { register, handleSubmit, formState: { errors } } = useForm<VerifyFormData>({
		resolver: zodResolver(verifySchema),
	});

	const verifyMutation = useMutation({
		mutationFn: (data: VerifyFormData) => verifyRequest({ email, code: data.code }),
		onSuccess: (data) => {
			setAccessToken(data.access_token);
			router.push("/");
		},
	});

	const resendMutation = useMutation({
		mutationFn: () => resendCodeRequest(email),
	});

	const onSubmit = (data: VerifyFormData) => {
		verifyMutation.mutate(data);
	};

	return (
		<AuthCard
			title="Verify your email"
			description={
				email
					? `Enter the 6-digit code we sent to ${email}`
					: "Enter the 6-digit code sent to your email"
			}
			footer={
				<>
					Wrong email?{" "}
					<Link href="/sign-in" className="font-medium text-primary underline-offset-4 hover:underline">
						Go back
					</Link>
				</>
			}
		>
			<form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
				<div className="space-y-2">
					<Label htmlFor="code">Verification code</Label>
					<Input
						id="code"
						type="text"
						inputMode="numeric"
						maxLength={6}
						placeholder="123456"
						{...register("code")}
					/>
					{errors.code && (
						<p className="text-sm text-destructive">{errors.code.message}</p>
					)}
				</div>

				{verifyMutation.isError && (
					<p className="text-sm text-destructive">
						{verifyMutation.error.message}
					</p>
				)}

				<Button type="submit" className="w-full" disabled={verifyMutation.isPending}>
					{verifyMutation.isPending ? "Verifying..." : "Verify"}
				</Button>

				<div className="text-center">
					<button
						type="button"
						onClick={() => resendMutation.mutate()}
						disabled={resendMutation.isPending}
						className="text-sm font-medium text-primary underline-offset-4 hover:underline disabled:opacity-50"
					>
						{resendMutation.isPending ? "Sending..." : "Resend code"}
					</button>
					{resendMutation.isError && (
						<p className="mt-2 text-sm text-destructive">
							{resendMutation.error.message}
						</p>
					)}
					{resendMutation.isSuccess && (
						<p className="mt-2 text-sm text-muted-foreground">
							A new code has been sent.
						</p>
					)}
				</div>
			</form>
		</AuthCard>
	);
}

export default function VerifyPage() {
	return (
		<Suspense fallback={null}>
			<VerifyPageContent />
		</Suspense>
	);
}
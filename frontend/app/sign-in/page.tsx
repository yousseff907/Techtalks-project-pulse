"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AuthCard } from "@/components/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const signInSchema = z.object({
	email: z.string().email("Please enter a valid email address"),
});

type SignInFormData = z.infer<typeof signInSchema>;

async function loginRequest(data: SignInFormData) {
	const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(data),
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail);
	}

	return response.json();
}

export default function SignInPage() {
	const router = useRouter();

	const { register, handleSubmit, getValues, formState: { errors } } = useForm<SignInFormData>({
		resolver: zodResolver(signInSchema),
	});

	const loginMutation = useMutation({
		mutationFn: loginRequest,
		onSuccess: () => {
			const email = getValues("email");
			router.push(`/verify?email=${encodeURIComponent(email)}`);
		},
	});

	const onSubmit = (data: SignInFormData) => {
		loginMutation.mutate(data);
	};

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
			<form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
				<div className="space-y-2">
					<Label htmlFor="email">Email address</Label>
					<Input
						id="email"
						type="email"
						placeholder="you@company.com"
						{...register("email")}
					/>
					{errors.email && (
						<p className="text-sm text-destructive">{errors.email.message}</p>
					)}
				</div>

				{loginMutation.isError && (
					<p className="text-sm text-destructive">
						{loginMutation.error.message}
					</p>
				)}

				<Button type="submit" className="w-full" disabled={loginMutation.isPending}>
					{loginMutation.isPending ? "Sending..." : "Send verification code"}
				</Button>
			</form>
		</AuthCard>
	);
}
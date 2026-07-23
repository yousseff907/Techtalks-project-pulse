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

const signUpSchema = z.object({
	username: z.string().min(1, "Full name is required"),
	email: z.string().email("Please enter a valid email address"),
});

type SignUpFormData = z.infer<typeof signUpSchema>;

async function registerRequest(data: SignUpFormData) {
	const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/register`, {
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

export default function SignUpPage() {
	const router = useRouter();

	const { register, handleSubmit, getValues, formState: { errors } } = useForm<SignUpFormData>({
		resolver: zodResolver(signUpSchema),
	});

	const registerMutation = useMutation({
		mutationFn: registerRequest,
		onSuccess: () => {
			const email = getValues("email");
			router.push(`/verify?email=${encodeURIComponent(email)}`);
		},
	});

	const onSubmit = (data: SignUpFormData) => {
		registerMutation.mutate(data);
	};

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
			<form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
				<div className="space-y-2">
					<Label htmlFor="username">Full name</Label>
					<Input
						id="username"
						placeholder="Alex Morgan"
						{...register("username")}
						className="border border-border shadow-sm"
					/>
					{errors.username && (
						<p className="text-sm text-destructive">{errors.username.message}</p>
					)}
				</div>

				<div className="space-y-2">
					<Label htmlFor="email">Email address</Label>
					<Input
						id="email"
						type="email"
						placeholder="you@company.com"
						{...register("email")}
						className="border border-border shadow-sm"
					/>
					{errors.email && (
						<p className="text-sm text-destructive">{errors.email.message}</p>
					)}
				</div>

				{registerMutation.isError && (
					<p className="text-sm text-destructive">
						{registerMutation.error.message}
					</p>
				)}

				<Button type="submit" className="w-full" disabled={registerMutation.isPending}>
					{registerMutation.isPending ? "Creating account..." : "Create account"}
				</Button>
			</form>
		</AuthCard>
	);
}
"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/lib/auth-store";

interface UserProfile {
	id: number;
	username: string;
	email: string;
	is_verified: boolean;
	created_at: string;
}

const usernameSchema = z.object({
	username: z.string().min(1, "Username cannot be blank"),
});

type UsernameFormData = z.infer<typeof usernameSchema>;

function authHeaders(token: string | null) {
	return {
		"Content-Type": "application/json",
		...(token ? { Authorization: `Bearer ${token}` } : {}),
	};
}

const mockProfile: UserProfile = {
	id: 1,
	username: "Alex Morgan",
	email: "alex@company.com",
	is_verified: true,
	created_at: "2026-06-22T14:30:00.000Z",
};

async function fetchProfile(token: string | null): Promise<UserProfile> {
	// Temporary until backend integration
	return Promise.resolve(mockProfile);
	/*
	const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/me`, {
		method: "GET",
		headers: authHeaders(token),
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail ?? "Failed to load profile");
	}

	return response.json();
	*/
}

async function updateUsername(token: string | null, username: string) {
	// Temporary until backend integration
	return Promise.resolve({ id: mockProfile.id, username });
	/*
	const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/me`, {
		method: "PATCH",
		headers: authHeaders(token),
		body: JSON.stringify({ username }),
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail);
	}

	return response.json();
	*/
}

async function deleteAccount(token: string | null) {
	// Temporary until backend integration
	return Promise.resolve({ message: "Account deleted successfully" });
	/*
	const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/me`, {
		method: "DELETE",
		headers: authHeaders(token),
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail);
	}

	return response.json();
	*/
}

export default function ProfilePage() {
	const router = useRouter();
	const queryClient = useQueryClient();
	const accessToken = useAuthStore((state) => state.accessToken);
	const clearAccessToken = useAuthStore((state) => state.clearAccessToken);
	const [confirmingDelete, setConfirmingDelete] = useState(false);

	const {
		data: profile,
		isLoading,
		isError,
		error,
	} = useQuery({
		queryKey: ["profile"],
		queryFn: () => fetchProfile(accessToken),
		// enabled: !!accessToken, // temporarily disabled for mock testing
	});

	const {
		register,
		handleSubmit,
		reset,
		formState: { errors },
	} = useForm<UsernameFormData>({
		resolver: zodResolver(usernameSchema),
	});

	useEffect(() => {
		if (profile) {
			reset({ username: profile.username });
		}
	}, [profile, reset]);

	const usernameMutation = useMutation({
		mutationFn: (data: UsernameFormData) => updateUsername(accessToken, data.username),
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ["profile"] });
		},
	});

	const deleteMutation = useMutation({
		mutationFn: () => deleteAccount(accessToken),
		onSuccess: () => {
			clearAccessToken();
			router.push("/sign-in");
		},
	});

	const onSubmitUsername = (data: UsernameFormData) => {
		usernameMutation.mutate(data);
	};

	const handleLogout = () => {
		clearAccessToken();
		router.push("/sign-in");
	};

	// Temporarily disabled while using mock data, restore once backend is connected
	// if (!accessToken) {
	// 	return (
	// 		<main className="mx-auto max-w-2xl p-8">
	// 			<Card>
	// 				<CardContent className="p-8">
	// 					<p>You need to be signed in to view this page.</p>
	// 				</CardContent>
	// 			</Card>
	// 		</main>
	// 	);
	// }

	return (
		<main className="mx-auto max-w-2xl space-y-6 p-8">
			<div>
				<h1 className="text-3xl font-bold">Profile & Settings</h1>
				<p className="text-muted-foreground">Manage your account details.</p>
			</div>

			{isLoading && (
				<Card>
					<CardContent className="p-8">
						<p>Loading profile...</p>
					</CardContent>
				</Card>
			)}

			{isError && (
				<Card>
					<CardContent className="p-8">
						<p className="text-destructive">{error.message}</p>
					</CardContent>
				</Card>
			)}

			{profile && (
				<>
					<Card>
						<CardContent className="space-y-4 p-6">
							<div>
								<p className="text-sm text-muted-foreground">Email</p>
								<p className="font-medium">{profile.email}</p>
							</div>
							<div>
								<p className="text-sm text-muted-foreground">Verified</p>
								<p className="font-medium">{profile.is_verified ? "Yes" : "No"}</p>
							</div>
							<div>
								<p className="text-sm text-muted-foreground">Member since</p>
								<p className="font-medium">
									{new Date(profile.created_at).toLocaleDateString()}
								</p>
							</div>
						</CardContent>
					</Card>

					<Card>
						<CardContent className="p-6">
							<h2 className="mb-4 text-lg font-semibold">Edit username</h2>
							<form onSubmit={handleSubmit(onSubmitUsername)} className="space-y-4">
								<div className="space-y-2">
									<Label htmlFor="username">Username</Label>
									<Input
										id="username"
										className="border border-border shadow-sm"
										{...register("username")}
									/>
									{errors.username && (
										<p className="text-sm text-destructive">{errors.username.message}</p>
									)}
								</div>

								{usernameMutation.isError && (
									<p className="text-sm text-destructive">
										{usernameMutation.error.message}
									</p>
								)}

								{usernameMutation.isSuccess && (
									<p className="text-sm text-muted-foreground">Username updated.</p>
								)}

								<Button type="submit" disabled={usernameMutation.isPending}>
									{usernameMutation.isPending ? "Saving..." : "Save changes"}
								</Button>
							</form>
						</CardContent>
					</Card>

					<Card>
						<CardContent className="p-6">
							<h2 className="mb-4 text-lg font-semibold">Session</h2>
							<Button variant="outline" onClick={handleLogout}>
								Log out
							</Button>
						</CardContent>
					</Card>

					<Card className="border-destructive">
						<CardContent className="p-6">
							<h2 className="mb-2 text-lg font-semibold text-destructive">Danger zone</h2>
							<p className="mb-4 text-sm text-muted-foreground">
								Deleting your account is permanent and cannot be undone.
							</p>

							{deleteMutation.isError && (
								<p className="mb-4 text-sm text-destructive">
									{deleteMutation.error.message}
								</p>
							)}

							{!confirmingDelete ? (
								<Button variant="destructive" onClick={() => setConfirmingDelete(true)}>
									Delete account
								</Button>
							) : (
								<div className="space-y-3">
									<p className="text-sm font-medium">
										Are you sure? This cannot be undone.
									</p>
									<div className="flex gap-2">
										<Button
											variant="destructive"
											disabled={deleteMutation.isPending}
											onClick={() => deleteMutation.mutate()}
										>
											{deleteMutation.isPending ? "Deleting..." : "Yes, delete my account"}
										</Button>
										<Button
											variant="outline"
											disabled={deleteMutation.isPending}
											onClick={() => setConfirmingDelete(false)}
										>
											Cancel
										</Button>
									</div>
								</div>
							)}
						</CardContent>
					</Card>
				</>
			)}
		</main>
	);
}
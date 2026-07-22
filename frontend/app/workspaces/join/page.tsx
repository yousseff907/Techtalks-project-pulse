"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AuthCard } from "@/components/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/lib/auth-store";

// Invite links are `${APP_BASE_URL}/${invite_code}`, but the backend matches
// only the bare code, so accept either and send the last path segment.
const joinWorkspaceSchema = z.object({
	invite_code: z
		.string()
		.transform((value) => value.trim().replace(/\/+$/, "").split("/").pop() ?? "")
		.refine((value) => value.length > 0, "Invite code cannot be blank"),
});

type JoinWorkspaceFormInput = z.input<typeof joinWorkspaceSchema>;
type JoinWorkspaceFormData = z.output<typeof joinWorkspaceSchema>;

interface JoinWorkspaceResponse {
	workspace_id: number;
	name: string;
}

async function joinWorkspaceRequest(
	data: JoinWorkspaceFormData,
	accessToken: string | null
): Promise<JoinWorkspaceResponse> {
	const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/workspaces/join`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
		},
		body: JSON.stringify(data),
	});

	if (!response.ok) {
		const error = await response.json().catch(() => null);
		throw new Error(error?.detail ?? "Failed to join workspace");
	}

	return response.json();
}

export default function JoinWorkspacePage() {
	const router = useRouter();
	const queryClient = useQueryClient();
	const accessToken = useAuthStore((state) => state.accessToken);

	const { register, handleSubmit, formState: { errors } } = useForm<
		JoinWorkspaceFormInput,
		unknown,
		JoinWorkspaceFormData
	>({
		resolver: zodResolver(joinWorkspaceSchema),
	});

	const joinWorkspaceMutation = useMutation({
		mutationFn: (data: JoinWorkspaceFormData) => joinWorkspaceRequest(data, accessToken),
		onSuccess: (data) => {
			queryClient.invalidateQueries({ queryKey: ["workspaces"] });
			router.push(`/workspaces/${data.workspace_id}/dashboard`);
		},
	});

	const onSubmit = (data: JoinWorkspaceFormData) => {
		joinWorkspaceMutation.mutate(data);
	};

	return (
		<AuthCard
			title="Join a workspace"
			description="Enter the invite code you received to join an existing workspace."
			footer={
				<>
					Want to create a workspace instead?{" "}
					<Link
						href="/workspaces/create"
						className="font-medium text-primary underline-offset-4 hover:underline"
					>
						Create one
					</Link>
				</>
			}
		>
			<form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
				<div className="space-y-2">
					<Label htmlFor="invite_code">Invite code</Label>
					<Input
						id="invite_code"
						placeholder="Paste your invite code or link"
						className="border border-border shadow-sm"
						{...register("invite_code")}
					/>
					{errors.invite_code && (
						<p className="text-sm text-destructive">{errors.invite_code.message}</p>
					)}
				</div>

				{joinWorkspaceMutation.isError && (
					<p className="text-sm text-destructive">
						{joinWorkspaceMutation.error.message}
					</p>
				)}

				<Button type="submit" className="w-full" disabled={joinWorkspaceMutation.isPending}>
					{joinWorkspaceMutation.isPending ? "Joining workspace..." : "Join workspace"}
				</Button>
			</form>
		</AuthCard>
	);
}

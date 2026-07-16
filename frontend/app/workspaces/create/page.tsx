"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AuthCard } from "@/components/auth-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuthStore } from "@/lib/auth-store";

const createWorkspaceSchema = z.object({
	name: z
		.string()
		.refine((value) => value.trim().length > 0, "Workspace name cannot be blank"),
});

type CreateWorkspaceFormData = z.infer<typeof createWorkspaceSchema>;

interface CreateWorkspaceResponse {
	workspace_id: number;
	name: string;
	invite_code: string;
	invite_link: string;
}

async function createWorkspaceRequest(
	data: CreateWorkspaceFormData,
	accessToken: string | null
): Promise<CreateWorkspaceResponse> {
	const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/workspaces`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
		},
		body: JSON.stringify(data),
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail);
	}

	return response.json();
}

export default function CreateWorkspacePage() {
	const router = useRouter();
	const accessToken = useAuthStore((state) => state.accessToken);

	const { register, handleSubmit, formState: { errors } } = useForm<CreateWorkspaceFormData>({
		resolver: zodResolver(createWorkspaceSchema),
	});

	const createWorkspaceMutation = useMutation({
		mutationFn: (data: CreateWorkspaceFormData) => createWorkspaceRequest(data, accessToken),
		onSuccess: (data) => {
			router.push(`/workspaces/${data.workspace_id}`);
		},
	});

	const onSubmit = (data: CreateWorkspaceFormData) => {
		createWorkspaceMutation.mutate(data);
	};

	return (
		<AuthCard
			title="Create your workspace"
			description="Give your workspace a name to start aggregating your team's Jira and Notion data."
			footer="You can create up to 5 workspaces."
		>
			<form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
				<div className="space-y-2">
					<Label htmlFor="name">Workspace name</Label>
					<Input
						id="name"
						placeholder="Acme Engineering"
						className="border border-border shadow-sm"
						{...register("name")}
					/>
					{errors.name && (
						<p className="text-sm text-destructive">{errors.name.message}</p>
					)}
				</div>

				{createWorkspaceMutation.isError && (
					<p className="text-sm text-destructive">
						{createWorkspaceMutation.error.message}
					</p>
				)}

				<Button type="submit" className="w-full" disabled={createWorkspaceMutation.isPending}>
					{createWorkspaceMutation.isPending ? "Creating workspace..." : "Create workspace"}
				</Button>
			</form>
		</AuthCard>
	);
}

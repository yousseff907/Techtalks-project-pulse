"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

import { useAuthStore } from "@/lib/auth-store";

interface Workspace {
	id: number;
	name: string;
	role: string;
	member_count: number;
	created_at: string;
}

interface WorkspaceDetails {
	id: number;
	name: string;
	invite_code: string;
	invite_link: string;
	created_by: string;
	created_at: string;
	member_count: number;
}

function authHeaders(token: string | null) {
	return {
		"Content-Type": "application/json",
		...(token ? { Authorization: `Bearer ${token}` } : {}),
	};
}

// Mock data, temporary until backend integration
const mockWorkspaces: Workspace[] = [
	{
		id: 1,
		name: "Project Pulse",
		role: "owner",
		member_count: 12,
		created_at: "2026-06-22T14:30:00Z",
	},
	{
		id: 2,
		name: "Development",
		role: "admin",
		member_count: 6,
		created_at: "2026-07-04T14:23:00Z",
	},
	{
		id: 3,
		name: "Marketing",
		role: "member",
		member_count: 4,
		created_at: "2026-02-21T19:10:00Z",
	},
];

const mockWorkspaceDetails: Record<number, WorkspaceDetails> = {
	1: {
		id: 1,
		name: "Project Pulse",
		invite_code: "mock-code-abc123",
		invite_link: "https://projectpulse.app/mock-code-abc123",
		created_by: "Alex Morgan",
		created_at: "2026-06-22T14:30:00Z",
		member_count: 12,
	},
	2: {
		id: 2,
		name: "Development",
		invite_code: "mock-code-def456",
		invite_link: "https://projectpulse.app/mock-code-def456",
		created_by: "Alex Morgan",
		created_at: "2026-07-04T14:23:00Z",
		member_count: 6,
	},
	3: {
		id: 3,
		name: "Marketing",
		invite_code: "mock-code-ghi789",
		invite_link: "https://projectpulse.app/mock-code-ghi789",
		created_by: "Sarah Chen",
		created_at: "2026-02-21T19:10:00Z",
		member_count: 4,
	},
};

async function fetchWorkspaces(token: string | null): Promise<Workspace[]> {
	// Temporary until backend integration
	return Promise.resolve(mockWorkspaces);
	/*
	const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/workspaces`, {
		method: "GET",
		headers: authHeaders(token),
	});

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail ?? "Failed to load workspaces");
	}

	return response.json();
	*/
}

async function fetchWorkspaceDetails(
	token: string | null,
	workspaceId: number
): Promise<WorkspaceDetails> {
	// Temporary until backend integration
	return Promise.resolve(mockWorkspaceDetails[workspaceId]);
	/*
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}`,
		{
			method: "GET",
			headers: authHeaders(token),
		}
	);

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail ?? "Failed to load workspace details");
	}

	return response.json();
	*/
}

async function renameWorkspace(token: string | null, workspaceId: number, name: string) {
	// Temporary until backend integration
	return Promise.resolve({ workspace_id: workspaceId, name });
	/*
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}`,
		{
			method: "PATCH",
			headers: authHeaders(token),
			body: JSON.stringify({ name }),
		}
	);

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail);
	}

	return response.json();
	*/
}

async function regenerateInviteCode(token: string | null, workspaceId: number) {
	// Temporary until backend integration
	return Promise.resolve({
		workspace_id: workspaceId,
		invite_code: "mock-code-new" + Math.floor(Math.random() * 1000),
		invite_link: "https://projectpulse.app/mock-code-new" + Math.floor(Math.random() * 1000),
	});
	/*
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}/invite-code`,
		{
			method: "PATCH",
			headers: authHeaders(token),
		}
	);

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail);
	}

	return response.json();
	*/
}

async function deleteWorkspace(token: string | null, workspaceId: number) {
	// Temporary until backend integration
	return Promise.resolve({ message: "Workspace deleted successfully" });
	/*
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}`,
		{
			method: "DELETE",
			headers: authHeaders(token),
		}
	);

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail);
	}

	return response.json();
	*/
}

async function leaveWorkspace(token: string | null, workspaceId: number) {
	// Temporary until backend integration
	return Promise.resolve({ message: "Successfully left the workspace" });
	/*
	const response = await fetch(
		`${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}/leave`,
		{
			method: "DELETE",
			headers: authHeaders(token),
		}
	);

	if (!response.ok) {
		const error = await response.json();
		throw new Error(error.detail);
	}

	return response.json();
	*/
}

const renameSchema = z.object({
	name: z.string().trim().min(1, "Workspace name cannot be blank"),
});

type RenameFormData = z.infer<typeof renameSchema>;

// Simple overlay modal, no external Dialog primitive assumed to exist.
function Modal({
	title,
	onClose,
	children,
}: {
	title: string;
	onClose: () => void;
	children: React.ReactNode;
}) {
	return (
		<div
			className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4"
			onClick={onClose}
		>
			<div
				className="w-full max-w-md rounded-lg border border-border bg-background p-6 shadow-lg"
				onClick={(e) => e.stopPropagation()}
			>
				<div className="mb-4 flex items-center justify-between">
					<h2 className="text-lg font-semibold">{title}</h2>
					<button
						onClick={onClose}
						className="text-muted-foreground hover:text-foreground"
						aria-label="Close"
					>
						✕
					</button>
				</div>
				{children}
			</div>
		</div>
	);
}

import { useRef } from "react";
import { createPortal } from "react-dom";

function WorkspaceActionsMenu({
	workspace,
	accessToken,
	onOpenRename,
	onOpenShare,
	onOpenDelete,
	onOpenLeave,
}: {
	workspace: Workspace;
	accessToken: string | null;
	onOpenRename: () => void;
	onOpenShare: () => void;
	onOpenDelete: () => void;
	onOpenLeave: () => void;
}) {
	const [open, setOpen] = useState(false);
	const buttonRef = useRef<HTMLButtonElement>(null);
	const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 });

	const toggle = (e: React.MouseEvent) => {
		e.stopPropagation();
		if (buttonRef.current) {
			const rect = buttonRef.current.getBoundingClientRect();
			setMenuPosition({
				top: rect.bottom + window.scrollY + 4,
				left: rect.right + window.scrollX - 192, // 192px = menu width (w-48)
			});
		}
		setOpen((prev) => !prev);
	};

	const withStop = (fn: () => void) => (e: React.MouseEvent) => {
		e.stopPropagation();
		setOpen(false);
		fn();
	};

	return (
		<div onClick={(e) => e.stopPropagation()}>
			<Button ref={buttonRef} variant="outline" size="sm" onClick={toggle}>
				⋮
			</Button>

			{open &&
				createPortal(
					<>
						{/* Invisible backdrop to close the menu on outside click */}
						<div
							className="fixed inset-0 z-40"
							onClick={() => setOpen(false)}
						/>
						<div
							className="fixed z-50 w-48 rounded-md border border-border bg-background shadow-lg"
							style={{ top: menuPosition.top, left: menuPosition.left }}
						>
							{workspace.role === "owner" && (
								<button
									className="block w-full px-4 py-2 text-left text-sm hover:bg-muted"
									onClick={withStop(onOpenRename)}
								>
									Rename Workspace
								</button>
							)}
							{workspace.role === "admin" && (
								<button
									className="block w-full px-4 py-2 text-left text-sm hover:bg-muted"
									onClick={withStop(onOpenRename)}
								>
									Rename Workspace
								</button>
							)}
							{(workspace.role === "owner" || workspace.role === "admin") && (
								<button
									className="block w-full px-4 py-2 text-left text-sm hover:bg-muted"
									onClick={withStop(onOpenShare)}
								>
									Share Workspace
								</button>
							)}
							{workspace.role === "owner" && (
								<button
									className="block w-full px-4 py-2 text-left text-sm text-destructive hover:bg-muted"
									onClick={withStop(onOpenDelete)}
								>
									Delete Workspace
								</button>
							)}
							<button
								className="block w-full px-4 py-2 text-left text-sm text-destructive hover:bg-muted"
								onClick={withStop(onOpenLeave)}
							>
								Leave Workspace
							</button>
						</div>
					</>,
					document.body
				)}
		</div>
	);
}

export default function WorkspacesPage() {
	const router = useRouter();
	const queryClient = useQueryClient();
	const accessToken = useAuthStore((state) => state.accessToken);

	const [renameTarget, setRenameTarget] = useState<Workspace | null>(null);
	const [shareTarget, setShareTarget] = useState<Workspace | null>(null);
	const [deleteTarget, setDeleteTarget] = useState<Workspace | null>(null);
	const [leaveTarget, setLeaveTarget] = useState<Workspace | null>(null);

	const {
		data: workspaces,
		isLoading,
		isError,
		error,
	} = useQuery({
		queryKey: ["workspaces"],
		queryFn: () => fetchWorkspaces(accessToken),

		// Restore when backend is connected.
		// enabled: !!accessToken,
	});

	/*
	if (!accessToken) {
		return (
			<main className="mx-auto max-w-3xl p-8">
				<Card>
					<CardContent className="p-8">
						<p>You need to be signed in to view this page.</p>
					</CardContent>
				</Card>
			</main>
		);
	}
	*/

	return (
		<main className="mx-auto max-w-3xl space-y-6 p-8">
			<div className="flex items-center justify-between">
				<div>
					<h1 className="text-3xl font-bold">Your Workspaces</h1>
					<p className="text-muted-foreground">Select a workspace or create a new one.</p>
				</div>

				<Link href="/workspaces/create">
					<Button>Create Workspace</Button>
				</Link>
			</div>

			{isLoading && (
				<Card>
					<CardContent className="p-8">Loading workspaces...</CardContent>
				</Card>
			)}

			{isError && (
				<Card>
					<CardContent className="p-8">
						<p className="text-destructive">{error.message}</p>
					</CardContent>
				</Card>
			)}

			{workspaces && workspaces.length === 0 && (
				<Card>
					<CardContent className="space-y-4 p-8">
						<p>You don't belong to any workspaces yet.</p>
						<Link href="/workspaces/create">
							<Button>Create your first workspace</Button>
						</Link>
					</CardContent>
				</Card>
			)}

			{workspaces && workspaces.length > 0 && (
				<div className="space-y-4">
					{workspaces.map((workspace) => (
						<Card
							key={workspace.id}
							className="cursor-pointer transition hover:border-primary"
							onClick={() => router.push(`/workspaces/${workspace.id}`)}
						>
							<CardContent className="flex items-center justify-between p-6">
								<div>
									<p className="font-semibold">{workspace.name}</p>
									<p className="text-sm text-muted-foreground">Role: {workspace.role}</p>
									<p className="text-sm text-muted-foreground">
										{workspace.member_count} members • Created on{" "}
										{new Date(workspace.created_at).toLocaleDateString()}
									</p>
								</div>

								<div
									className="flex items-center gap-2"
									onClick={(e) => e.stopPropagation()}
								>
									<Button variant="outline" onClick={() => router.push(`/workspaces/${workspace.id}`)}>
										Open
									</Button>
									<WorkspaceActionsMenu
										workspace={workspace}
										accessToken={accessToken}
										onOpenRename={() => setRenameTarget(workspace)}
										onOpenShare={() => setShareTarget(workspace)}
										onOpenDelete={() => setDeleteTarget(workspace)}
										onOpenLeave={() => setLeaveTarget(workspace)}
									/>
								</div>
							</CardContent>
						</Card>
					))}
				</div>
			)}

			{renameTarget && (
				<RenameDialog
					workspace={renameTarget}
					accessToken={accessToken}
					onClose={() => setRenameTarget(null)}
					onSuccess={() => {
						setRenameTarget(null);
						queryClient.invalidateQueries({ queryKey: ["workspaces"] });
					}}
				/>
			)}

			{shareTarget && (
				<ShareDialog
					workspace={shareTarget}
					accessToken={accessToken}
					onClose={() => setShareTarget(null)}
				/>
			)}

			{deleteTarget && (
				<ConfirmDialog
					title="Delete Workspace"
					message={`Are you sure you want to delete "${deleteTarget.name}"? This cannot be undone.`}
					confirmLabel="Delete"
					onClose={() => setDeleteTarget(null)}
					onConfirm={async () => {
						await deleteWorkspace(accessToken, deleteTarget.id);
						setDeleteTarget(null);
						queryClient.invalidateQueries({ queryKey: ["workspaces"] });
					}}
				/>
			)}

			{leaveTarget && (
				<ConfirmDialog
					title="Leave Workspace"
					message={`Are you sure you want to leave "${leaveTarget.name}"?`}
					confirmLabel="Leave"
					onClose={() => setLeaveTarget(null)}
					onConfirm={async () => {
						await leaveWorkspace(accessToken, leaveTarget.id);
						setLeaveTarget(null);
						queryClient.invalidateQueries({ queryKey: ["workspaces"] });
					}}
				/>
			)}
		</main>
	);
}

function RenameDialog({
	workspace,
	accessToken,
	onClose,
	onSuccess,
}: {
	workspace: Workspace;
	accessToken: string | null;
	onClose: () => void;
	onSuccess: () => void;
}) {
	const {
		register,
		handleSubmit,
		formState: { errors },
	} = useForm<RenameFormData>({
		resolver: zodResolver(renameSchema),
		defaultValues: { name: workspace.name },
	});

	const renameMutation = useMutation({
		mutationFn: (data: RenameFormData) => renameWorkspace(accessToken, workspace.id, data.name),
		onSuccess,
	});

	return (
		<Modal title="Rename Workspace" onClose={onClose}>
			<form
				onSubmit={handleSubmit((data) => renameMutation.mutate(data))}
				className="space-y-4"
			>
				<div className="space-y-2">
					<Label htmlFor="rename-name">Workspace name</Label>
					<Input
						id="rename-name"
						className="border border-border shadow-sm"
						{...register("name")}
					/>
					{errors.name && (
						<p className="text-sm text-destructive">{errors.name.message}</p>
					)}
				</div>

				{renameMutation.isError && (
					<p className="text-sm text-destructive">{renameMutation.error.message}</p>
				)}

				<div className="flex justify-end gap-2">
					<Button type="button" variant="outline" onClick={onClose}>
						Cancel
					</Button>
					<Button type="submit" disabled={renameMutation.isPending}>
						{renameMutation.isPending ? "Saving..." : "Save"}
					</Button>
				</div>
			</form>
		</Modal>
	);
}

function ShareDialog({
	workspace,
	accessToken,
	onClose,
}: {
	workspace: Workspace;
	accessToken: string | null;
	onClose: () => void;
}) {
	const queryClient = useQueryClient();
	const [confirmingRegenerate, setConfirmingRegenerate] = useState(false);
	const [copied, setCopied] = useState(false);

	const {
		data: details,
		isLoading,
		isError,
		error,
	} = useQuery({
		queryKey: ["workspace-details", workspace.id],
		queryFn: () => fetchWorkspaceDetails(accessToken, workspace.id),
	});

	const regenerateMutation = useMutation({
		mutationFn: () => regenerateInviteCode(accessToken, workspace.id),
		onSuccess: () => {
			setConfirmingRegenerate(false);
			queryClient.invalidateQueries({ queryKey: ["workspace-details", workspace.id] });
		},
	});

	const canRegenerate = workspace.role === "owner" || workspace.role === "admin";

	const handleCopy = () => {
		if (!details) return;
		navigator.clipboard.writeText(details.invite_link);
		setCopied(true);
		setTimeout(() => setCopied(false), 2000);
	};

	return (
		<Modal title="Share Workspace" onClose={onClose}>
			{isLoading && <p>Loading...</p>}

			{isError && <p className="text-sm text-destructive">{error.message}</p>}

			{details && (
				<div className="space-y-4">
					<div className="space-y-2">
						<Label>Invite link</Label>
						<div className="flex gap-2">
							<Input
								readOnly
								className="border border-border shadow-sm"
								value={details.invite_link}
							/>
							<Button type="button" variant="outline" onClick={handleCopy}>
								{copied ? "Copied!" : "Copy URL"}
							</Button>
						</div>
					</div>

					<div className="space-y-2">
						<Label>Invite code</Label>
						<Input
							readOnly
							className="border border-border shadow-sm"
							value={details.invite_code}
						/>
					</div>

					{regenerateMutation.isError && (
						<p className="text-sm text-destructive">
							{regenerateMutation.error.message}
						</p>
					)}

					{canRegenerate && (
						<div className="border-t border-border pt-4">
							{!confirmingRegenerate ? (
								<Button
									type="button"
									variant="outline"
									onClick={() => setConfirmingRegenerate(true)}
								>
									Regenerate Invite Code
								</Button>
							) : (
								<div className="space-y-2">
									<p className="text-sm font-medium">
										The current link and code will stop working immediately. Continue?
									</p>
									<div className="flex gap-2">
										<Button
											type="button"
											variant="destructive"
											disabled={regenerateMutation.isPending}
											onClick={() => regenerateMutation.mutate()}
										>
											{regenerateMutation.isPending ? "Regenerating..." : "Yes, regenerate"}
										</Button>
										<Button
											type="button"
											variant="outline"
											disabled={regenerateMutation.isPending}
											onClick={() => setConfirmingRegenerate(false)}
										>
											Cancel
										</Button>
									</div>
								</div>
							)}
						</div>
					)}
				</div>
			)}
		</Modal>
	);
}

function ConfirmDialog({
	title,
	message,
	confirmLabel,
	onClose,
	onConfirm,
}: {
	title: string;
	message: string;
	confirmLabel: string;
	onClose: () => void;
	onConfirm: () => Promise<void>;
}) {
	const mutation = useMutation({
		mutationFn: onConfirm,
	});

	return (
		<Modal title={title} onClose={onClose}>
			<p className="mb-4 text-sm">{message}</p>

			{mutation.isError && (
				<p className="mb-4 text-sm text-destructive">
					{(mutation.error as Error).message}
				</p>
			)}

			<div className="flex justify-end gap-2">
				<Button type="button" variant="outline" onClick={onClose} disabled={mutation.isPending}>
					Cancel
				</Button>
				<Button
					type="button"
					variant="destructive"
					disabled={mutation.isPending}
					onClick={() => mutation.mutate()}
				>
					{mutation.isPending ? "Working..." : confirmLabel}
				</Button>
			</div>
		</Modal>
	);
}
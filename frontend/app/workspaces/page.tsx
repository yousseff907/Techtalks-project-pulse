"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { useQuery } from "@tanstack/react-query";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

import { useAuthStore } from "@/lib/auth-store";

interface Workspace {
	id: number;
	name: string;
	role: string;
	member_count: number;
	created_at: string;
}

function authHeaders(token: string | null) {
	return {
		"Content-Type": "application/json",
		...(token
			? { Authorization: `Bearer ${token}` }
			: {}),
	};
}

async function fetchWorkspaces(
    token: string | null
): Promise<Workspace[]> {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/workspaces`,
        {
            method: "GET",
            headers: authHeaders(token),
        }
    );

    if (response.status === 204) {
        return [];
    }

    if (!response.ok) {
        const error = await response.json();

        throw new Error(
            error.detail ??
            "Failed to load workspaces"
        );
    }

    return response.json();
}

export default function WorkspacesPage() {
	const router = useRouter();

	const accessToken = useAuthStore(
		(state) => state.accessToken
	);

	const {
		data: workspaces,
		isLoading,
		isError,
		error,
	} = useQuery({
		queryKey: ["workspaces"],
		queryFn: () => fetchWorkspaces(accessToken),
		enabled: !!accessToken,
	});

	if (!accessToken) {
		return (
			<main className="mx-auto max-w-3xl p-8">
				<Card>
					<CardContent className="p-8">
						<p>
							You need to be signed in
							to view this page.
						</p>
					</CardContent>
				</Card>
			</main>
		);
	}

	return (
		<main className="mx-auto max-w-3xl space-y-6 p-8">

			<div className="flex items-center justify-between">

				<div>
					<h1 className="text-3xl font-bold">
						Your Workspaces
					</h1>

					<p className="text-muted-foreground">
						Select a workspace or create a new one.
					</p>
				</div>

				<Link href="/workspaces/create">
					<Button>
						Create Workspace
					</Button>
				</Link>

			</div>

			{isLoading && (
				<Card>
					<CardContent className="p-8">
						Loading workspaces...
					</CardContent>
				</Card>
			)}

			{isError && (
				<Card>
					<CardContent className="p-8">
						<p className="text-destructive">
							{error.message}
						</p>
					</CardContent>
				</Card>
			)}

			{workspaces &&
				workspaces.length === 0 && (
					<Card>
						<CardContent className="space-y-4 p-8">

							<p>
								You don't belong to any
								workspaces yet.
							</p>

							<Link
								href="/workspaces/create"
							>
								<Button>
									Create your first workspace
								</Button>
							</Link>

						</CardContent>
					</Card>
				)}

			{workspaces &&
				workspaces.length > 0 && (
					<div className="space-y-4">

						{workspaces.map(
							(workspace) => (
								<Card
									key={workspace.id}
									className="cursor-pointer transition hover:border-primary"
									onClick={() =>
										router.push(
											`/workspaces/${workspace.id}`
										)
									}
								>
									<CardContent className="flex items-center justify-between p-6">

										<div>
											<p className="font-semibold">
												{workspace.name}
											</p>

											<p className="text-sm text-muted-foreground">
												Role: {workspace.role}
											</p>

											<p className="text-sm text-muted-foreground">
												{workspace.member_count} members • Created on{" "}
												{new Date(
													workspace.created_at
												).toLocaleDateString()}
											</p>
										</div>

										<Button
											variant="outline"
										>
											Open
										</Button>

									</CardContent>
								</Card>
							)
						)}

					</div>
				)}

		</main>
	);
}
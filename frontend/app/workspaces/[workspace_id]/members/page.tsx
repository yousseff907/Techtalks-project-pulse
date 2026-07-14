"use client";

import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

import { mockMembers, WorkspaceMember } from "./mock";

async function fetchWorkspaceMembers(
	workspaceId: string,
): Promise<WorkspaceMember[]> {
	// Temporary until backend integration
	return Promise.resolve(mockMembers);

	/*
	const response = await fetch(
	`${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}/members`
);

    if (!response.ok) {
        const error = await response.json();

        throw new Error(
            error.detail ?? "Failed to fetch workspace members"
        );
    }

    return response.json();
	*/
}

export default function MembersPage() {
	const params = useParams();
	const workspaceId = params.workspace_id as string;

	const [search, setSearch] = useState("");

    const [sortBy, setSortBy] = useState<"username" | "role">("username");
    const [ascending, setAscending] = useState(true);

	const {
		data: members = [],
		isLoading,
		isError,
		error,
	} = useQuery({
		queryKey: ["workspace-members", workspaceId],
		queryFn: () => fetchWorkspaceMembers(workspaceId),
	});

	const filteredMembers = useMemo(() => {
        const term = search.toLowerCase().trim();

        let filtered = members;

        if (term) {
            filtered = members.filter((member) => (
                member.username.toLowerCase().includes(term) ||
                member.email.toLowerCase().includes(term) ||
                member.role.toLowerCase().includes(term) ||
                member.jira?.name.toLowerCase().includes(term) ||
                member.jira?.email.toLowerCase().includes(term) ||
                member.notion?.name.toLowerCase().includes(term) ||
                member.notion?.email.toLowerCase().includes(term)
            ));
        }

        return [...filtered].sort((a, b) => {
            const left = a[sortBy].toLowerCase();
            const right = b[sortBy].toLowerCase();

            if (left < right) return ascending ? -1 : 1;
            if (left > right) return ascending ? 1 : -1;
            return 0;
        });
    }, [members, search, sortBy, ascending]);

	return (
		<main className="mx-auto max-w-7xl p-8">
			<div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
				<div>
					<h1 className="text-3xl font-bold">
						Team Members
					</h1>

					<p className="text-muted-foreground">
						Manage workspace members and linked platform accounts.
					</p>
				</div>

				<div className="text-sm text-muted-foreground">
					{filteredMembers.length} member
					{filteredMembers.length !== 1 ? "s" : ""}
				</div>
			</div>

			<div className="mt-6">
				<Input
                    className="border border-border shadow-sm"
                    placeholder="Search members..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                />
			</div>

			{isLoading && (
				<Card className="mt-6">
					<CardContent className="p-8">
						<p>Loading members...</p>
					</CardContent>
				</Card>
			)}

			{isError && (
				<Card className="mt-6">
					<CardContent className="p-8">
						<p className="text-destructive">
							{error.message}
						</p>
					</CardContent>
				</Card>
			)}

			{!isLoading &&
				!isError &&
				filteredMembers.length === 0 && (
					<Card className="mt-6">
						<CardContent className="flex flex-col items-center justify-center py-12">
							<h2 className="text-lg font-semibold">
								No members found
							</h2>

							<p className="mt-2 text-center text-muted-foreground">
								Try adjusting your search or invite members to your workspace.
							</p>
						</CardContent>
					</Card>
				)}

			{!isLoading &&
				!isError &&
				filteredMembers.length > 0 && (
					<Card className="mt-6 overflow-hidden p-0">
	                    <CardContent className="p-0">
                            <div className="overflow-x-auto">
                                <table className="w-full border-collapse">
                                    <thead className="bg-muted/60">
                                        <tr className="border-b">
                                            <th
                                                onClick={() => {
                                                    if (sortBy === "username") {
                                                        setAscending(!ascending);
                                                    } else {
                                                        setSortBy("username");
                                                        setAscending(true);
                                                    }
                                                }}
                                                className="cursor-pointer px-6 py-4 text-left text-sm font-semibold select-none hover:bg-muted"
                                            >
                                                Member {sortBy === "username" && (ascending ? "↑" : "↓")}
                                            </th>

                                            <th
                                                onClick={() => {
                                                    if (sortBy === "role") {
                                                        setAscending(!ascending);
                                                    } else {
                                                        setSortBy("role");
                                                        setAscending(true);
                                                    }
                                                }}
                                                className="cursor-pointer px-6 py-4 text-center text-sm font-semibold select-none hover:bg-muted"
                                            >
                                                Role {sortBy === "role" && (ascending ? "↑" : "↓")}
                                            </th>

                                            <th className="px-6 py-4 text-center text-sm font-semibold">
                                                Jira
                                            </th>

                                            <th className="px-6 py-4 text-center text-sm font-semibold">
                                                Notion
                                            </th>
                                        </tr>
                                    </thead>

                                    <tbody>
                                        {filteredMembers.map((member) => (
                                            <tr
                                                key={member.id}
                                                className="border-b transition-colors hover:bg-muted/30"
                                            >
                                                <td className="px-6 py-5 align-middle">
                                                    <p className="font-medium">
                                                        {member.username}
                                                    </p>

                                                    <p className="text-sm text-muted-foreground">
                                                        {member.email}
                                                    </p>
                                                </td>

                                                <td className="px-6 py-5 text-center align-middle">
                                                    <span className="inline-flex rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
                                                        {member.role}
                                                    </span>
                                                </td>

                                                <td className="px-6 py-5 text-center align-middle">
                                                    {member.jira ? (
                                                        <div>
                                                            <span className="inline-flex rounded-full bg-green-100 px-2 py-1 text-xs font-semibold text-green-700">
                                                                Linked
                                                            </span>

                                                            <p className="text-sm">
                                                                {member.jira.name}
                                                            </p>

                                                            <p className="text-xs text-muted-foreground">
                                                                {member.jira.email}
                                                            </p>
                                                        </div>
                                                    ) : (
                                                        <span className="inline-flex rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">
                                                            Not Connected
                                                        </span>
                                                    )}
                                                </td>

                                                <td className="px-6 py-5 text-center align-middle">
                                                    {member.notion ? (
                                                        <div>
                                                            <span className="inline-flex rounded-full bg-green-100 px-2 py-1 text-xs font-semibold text-green-700">
                                                                Linked
                                                            </span>

                                                            <p className="text-sm">
                                                                {member.notion.name}
                                                            </p>

                                                            <p className="text-xs text-muted-foreground">
                                                                {member.notion.email}
                                                            </p>
                                                        </div>
                                                    ) : (
                                                        <span className="inline-flex rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-600">
                                                            Not Connected
                                                        </span>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
					</Card>
				)}
		</main>
	);
}
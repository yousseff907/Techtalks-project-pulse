"use client";

import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import {useMutation, useQuery, useQueryClient,} from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuthStore } from "@/lib/auth-store";
import { Button } from "@/components/ui/button";
import { createPortal } from "react-dom";
import { useRef } from "react";



export interface ProviderAccount {
	id: string;
	name: string;
	email: string;
}

export interface WorkspaceMember {
	id: number;
	username: string;
	email: string;
	role: string;
	jira: ProviderAccount | null;
	notion: ProviderAccount | null;
}

interface CurrentUser {
    id: number;
    username: string;
    email: string;
    is_verified: boolean;
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


async function fetchWorkspaceMembers(
	workspaceId: string,
    token: string | null,
): Promise<WorkspaceMember[]> {
	
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}/members`,
        {
            headers: authHeaders(token),
        }
    );

    if (!response.ok) {
        const error = await response.json();

        throw new Error(
            error.detail ??
            "Failed to fetch workspace members"
        );
    }

    return response.json();
}

async function fetchCurrentUser(
    token: string | null,
): Promise<CurrentUser> {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/users/me`,
        {
            headers: authHeaders(token),
        }
    );

    if (!response.ok) {
        const error = await response.json();

        throw new Error(
            error.detail ?? "Failed to fetch user"
        );
    }

    return response.json();
}

async function updateMemberRole(
    workspaceId: string,
    userId: number,
    role: "admin" | "member",
    token: string | null,
) {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}/members/${userId}`,
        {
            method: "PATCH",
            headers: authHeaders(token),
            body: JSON.stringify({ role }),
        }
    );

    if (!response.ok) {
        const error = await response.json();

        throw new Error(
            error.detail ?? "Failed to update member"
        );
    }

    return response.json();
}

async function removeMember(
    workspaceId: string,
    userId: number,
    token: string | null,
) {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}/members/${userId}`,
        {
            method: "DELETE",
            headers: authHeaders(token),
        }
    );

    if (!response.ok) {
        const error = await response.json();

        throw new Error(
            error.detail ?? "Failed to remove member"
        );
    }

    return response.json();
}


function MemberActionsMenu({
    member,
    viewerRole,
    currentUserId,
    roleMutation,
    removeMutation,
    confirmRemoveId,
    setConfirmRemoveId,
}: {
    member: WorkspaceMember;
    viewerRole?: string;
    currentUserId?: number;
    roleMutation: any;
    removeMutation: any;
    confirmRemoveId: number | null;
    setConfirmRemoveId: React.Dispatch<React.SetStateAction<number | null>>;
}) {
    const [open, setOpen] = useState(false);

    const buttonRef = useRef<HTMLButtonElement>(null);

    const [menuPosition, setMenuPosition] = useState({
        top: 0,
        left: 0,
    });

    if (
        member.id === currentUserId ||
        member.role === "owner" ||
        (viewerRole !== "owner" && viewerRole !== "admin")
    ) {
        return null;
    }

    const toggle = (e: React.MouseEvent) => {
        e.stopPropagation();

        if (buttonRef.current) {
            const rect = buttonRef.current.getBoundingClientRect();

            setMenuPosition({
                top: rect.bottom + window.scrollY + 4,
                left: rect.right + window.scrollX - 200,
            });
        }

        setOpen((prev) => !prev);
    };

    return (
        <>
            <Button
                ref={buttonRef}
                size="sm"
                variant="outline"
                onClick={toggle}
            >
                ⋮
            </Button>

            {open &&
                createPortal(
                    <>
                        <div
                            className="fixed inset-0 z-40"
                            onClick={() => setOpen(false)}
                        />

                        <div
                            className="fixed z-50 w-52 rounded-md border border-border bg-background shadow-lg"
                            style={{
                                top: menuPosition.top,
                                left: menuPosition.left,
                            }}
                        >
                            {member.role === "member" && (
                                <button
                                    className="block w-full px-4 py-2 text-left text-sm hover:bg-muted"
                                    onClick={() => {
                                        setOpen(false);

                                        roleMutation.mutate({
                                            userId: member.id,
                                            role: "admin",
                                        });
                                    }}
                                >
                                    Promote to Admin
                                </button>
                            )}

                            {member.role === "admin" && (
                                <button
                                    className="block w-full px-4 py-2 text-left text-sm hover:bg-muted"
                                    onClick={() => {
                                        setOpen(false);

                                        roleMutation.mutate({
                                            userId: member.id,
                                            role: "member",
                                        });
                                    }}
                                >
                                    Demote Admin
                                </button>
                            )}

                            <button
                                className="block w-full px-4 py-2 text-left text-sm text-destructive hover:bg-muted"
                                onClick={() => {
                                    setOpen(false);
                                    setConfirmRemoveId(member.id);
                                }}
                            >
                                Remove from Workspace
                            </button>
                        </div>
                    </>,
                    document.body
                )}

            {confirmRemoveId === member.id && (
                <div className="mt-2 flex flex-col items-center gap-2">
                    <p className="text-center text-xs">
                        Remove this member?
                    </p>

                    <div className="flex gap-2">
                        <Button
                            size="sm"
                            variant="destructive"
                            onClick={() =>
                                removeMutation.mutate(member.id)
                            }
                        >
                            Confirm
                        </Button>

                        <Button
                            size="sm"
                            variant="outline"
                            onClick={() =>
                                setConfirmRemoveId(null)
                            }
                        >
                            Cancel
                        </Button>
                    </div>
                </div>
            )}
        </>
    );
}

export default function MembersPage() {
	const params = useParams();
	const workspaceId = params.workspace_id as string;

    const accessToken = useAuthStore(
        (state) => state.accessToken
    );

    const queryClient = useQueryClient();

	const [search, setSearch] = useState("");

    const [sortBy, setSortBy] = useState<"username" | "role">("username");
    const [ascending, setAscending] = useState(true);
    
    const [confirmRemoveId, setConfirmRemoveId] = useState<number | null>(null);

	const {
		data: members = [],
		isLoading,
		isError,
		error,
	} = useQuery({
		queryKey: ["workspace-members", workspaceId],
		queryFn: () =>
        fetchWorkspaceMembers(
                workspaceId,
                accessToken
            ),
        enabled: !!accessToken,
	});

    const { data: currentUser } = useQuery({
        queryKey: ["current-user"],
        queryFn: () => fetchCurrentUser(accessToken),
        enabled: !!accessToken,
    });

    const roleMutation = useMutation({
        mutationFn: ({
            userId,
            role,
        }: {
            userId: number;
            role: "admin" | "member";
        }) =>
            updateMemberRole(
                workspaceId,
                userId,
                role,
                accessToken
            ),

        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ["workspace-members", workspaceId],
            });
        },
    });

    const removeMutation = useMutation({
        mutationFn: (userId: number) =>
            removeMember(
                workspaceId,
                userId,
                accessToken
            ),
        onSuccess: () => {
            setConfirmRemoveId(null);

            queryClient.invalidateQueries({
                queryKey: ["workspace-members", workspaceId],
            });
        },
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


    const viewerRole = members.find(
        (member) => member.id === currentUser?.id
    )?.role;


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

                                            <th className="px-6 py-4 text-center text-sm font-semibold">
                                                Actions
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
                                                
                                                <td className="px-6 py-5 text-center align-middle">
                                                    <MemberActionsMenu
                                                        member={member}
                                                        viewerRole={viewerRole}
                                                        currentUserId={currentUser?.id}
                                                        roleMutation={roleMutation}
                                                        removeMutation={removeMutation}
                                                        confirmRemoveId={confirmRemoveId}
                                                        setConfirmRemoveId={setConfirmRemoveId}
                                                    />
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
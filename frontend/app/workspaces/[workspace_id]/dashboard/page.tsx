"use client";

import { useMemo, useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
    useMutation,
    useQuery,
    useQueryClient,
} from "@tanstack/react-query";

import { useAuthStore } from "@/lib/auth-store";

import { Card, CardContent } from "@/components/ui/card";
import { AppSidebar } from "@/components/dashboard/app-sidebar";
import { DashboardTopBar } from "@/components/dashboard/dashboard-topbar";
import { StatCard } from "@/components/dashboard/stat-card";
import { RecentTasksTable } from "@/components/dashboard/recent-tasks-table";
import { SyncStatusCard } from "@/components/dashboard/sync-status-card";
import { AISummaryCard } from "@/components/dashboard/ai-summary-card";

import {
    ListTodo,
    CheckCircle2,
    Clock3,
    Users,
} from "lucide-react";

import { DashboardSkeleton } from "@/components/dashboard/dashboard-skeleton";

interface SyncStatus {
    last_synced_at: string | null;
}

interface SummaryResponse {
    summary: string;
}

interface Workspace {
    id: number;
    name: string;
    role: string;
    member_count: number;
}

interface DashboardResponse {
  total_tasks: number;
  by_status: {
    TODO: number;
    IN_PROGRESS: number;
    DONE: number;
  };
  by_source: Record<
    string,
    {
      TODO: number;
      IN_PROGRESS: number;
      DONE: number;
      total: number;
    }
  >;
  completion_rate: number;
  workload: Record<string, number>;
}

interface DashboardTask {
    id: number;
    integration_id: number;
    type: string;
    source: string;
    title: string | null;
    status: string | null;
    payload: {
        id?: string;
        key?: string;
        title?: string;
        assignee?: string;
        due_date?: string;
    } | null;
    fetched_at: string;
}

interface CurrentUser {
    id: number;
    username: string;
    email: string;
    is_verified: boolean;
    created_at: string;
}

async function fetchDashboard(
  workspaceId: string,
  token: string | null
): Promise<DashboardResponse> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}/dashboard`,
    {
      headers: authHeaders(token),
    }
  );

  if (!response.ok) {
    throw new Error("Failed to fetch dashboard");
  }

  return response.json();
}

async function fetchTasks(
    workspaceId: string,
    token: string | null
): Promise<DashboardTask[]> {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}/data?type=task`,
        {
            headers: authHeaders(token),
        }
    );

    if (!response.ok) {
        throw new Error("Failed to fetch tasks");
    }

    return response.json();
}

function authHeaders(token: string | null) {
    return {
        "Content-Type": "application/json",
        ...(token
            ? {
                  Authorization: `Bearer ${token}`,
              }
            : {}),
    };
}

async function fetchWorkspaces(
    token: string | null
): Promise<Workspace[]> {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/workspaces`,
        {
            headers: authHeaders(token),
        }
    );

    if (!response.ok) {
        throw new Error("Failed to fetch workspaces");
    }

    return response.json();
}

async function fetchSyncStatus(
    workspaceId: string,
    token: string | null
): Promise<SyncStatus> {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}/sync/status`,
        {
            headers: authHeaders(token),
        }
    );

    if (!response.ok) {
        throw new Error("Failed to fetch sync status");
    }

    return response.json();
}

async function fetchCurrentUser(
    token: string | null
): Promise<CurrentUser> {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/users/me`,
        {
            headers: authHeaders(token),
        }
    );

    if (!response.ok) {
        throw new Error("Failed to fetch current user");
    }

    return response.json();
}

async function triggerSync(
    workspaceId: string,
    token: string | null
) {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}/sync`,
        {
            method: "POST",
            headers: authHeaders(token),
        }
    );

    if (!response.ok) {
        const error = await response.json();

        throw new Error(
            error.detail ?? "Failed to trigger sync"
        );
    }

    return response.json();
}

async function generateSummary(
    workspaceId: string,
    token: string | null
): Promise<SummaryResponse> {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}/summary`,
        {
            method: "POST",
            headers: authHeaders(token),
        }
    );

    if (!response.ok) {
        const error = await response.json();

        throw new Error(
            error.detail ?? "Failed to generate summary"
        );
    }

    return response.json();
}

async function emailSummary(
    workspaceId: string,
    email: string | null,
    token: string | null
) {
    const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}/summary/email`,
        {
            method: "POST",
            headers: authHeaders(token),
            body: JSON.stringify({
                email,
            }),
        }
    );

    if (!response.ok) {
        const error = await response.json();

        throw new Error(
            error.detail ?? "Failed to send summary"
        );
    }

    return response.json();
}

export default function DashboardPage() {
    const params = useParams();
    const router = useRouter();

    const workspaceId = params.workspace_id as string;

    const accessToken = useAuthStore(
        (state) => state.accessToken
    );

    const queryClient = useQueryClient();

    const [summary, setSummary] = useState("");
    const [emailAddress, setEmailAddress] = useState("");
    const [search, setSearch] = useState("");

    const {
        data: syncStatus,
        isLoading: syncLoading,
        isError: syncError,
        error,
    } = useQuery({
        queryKey: ["sync-status", workspaceId],
        queryFn: () =>
            fetchSyncStatus(
                workspaceId,
                accessToken
            ),
        enabled: !!accessToken,
    });



    const syncMutation = useMutation({
        mutationFn: () =>
            triggerSync(
                workspaceId,
                accessToken
            ),

        onSuccess: () => {
            queryClient.invalidateQueries({
                queryKey: ["sync-status", workspaceId],
            });

            queryClient.invalidateQueries({
                queryKey: ["dashboard", workspaceId],
            });

            queryClient.invalidateQueries({
                queryKey: ["tasks", workspaceId],
            });
        },
    });

    const summaryMutation = useMutation({
        mutationFn: () =>
            generateSummary(
                workspaceId,
                accessToken
            ),

        onSuccess: (data) => {
            setSummary(data.summary);
        },
    });

    const emailMutation = useMutation({
        mutationFn: (email: string | null) =>
            emailSummary(
                workspaceId,
                email,
                accessToken
            ),

        onSuccess: () => {
            setEmailAddress("");
        },
    });

    const {
        data: currentUser,
        isLoading: currentUserLoading,
    } = useQuery({
        queryKey: ["current-user"],
        queryFn: () => fetchCurrentUser(accessToken),
        enabled: !!accessToken,
    });


    const {
        data: workspaces = [],
        isLoading: workspacesLoading,
    } = useQuery({
        queryKey: ["workspaces"],
        queryFn: () => fetchWorkspaces(accessToken),
        enabled: !!accessToken,
    });

    useEffect(() => {
        if (!accessToken) return;

        if (workspaces.length === 0) {
            router.replace("/workspaces/create");
            return;
        }

        const exists = workspaces.some(
            (workspace) =>
                workspace.id === Number(workspaceId)
        );

        if (!exists) {
            router.replace(
                `/workspaces/${workspaces[0].id}/dashboard`
            );
        }
    }, [workspaces, accessToken, workspaceId, router]);


    const currentWorkspace =
        workspaces.find(
            (workspace) =>
                workspace.id === Number(workspaceId)
        ) ?? workspaces[0];


    const {
        data: tasks = [],
        isLoading: tasksLoading,
    } = useQuery({
        queryKey: ["tasks", workspaceId],
        queryFn: () =>
            fetchTasks(
                workspaceId,
                accessToken
            ),
        enabled: !!accessToken,
    });


    

    const {
        data: dashboard,
        isLoading: dashboardLoading,
    } = useQuery({
        queryKey: ["dashboard", workspaceId],
        queryFn: () =>
            fetchDashboard(
                workspaceId,
                accessToken
            ),
        enabled: !!accessToken,
    });


    const filteredTasks = useMemo(() => {
        const term = search.trim().toLowerCase();

        if (!term) {
            return tasks;
        }

        return tasks.filter((task) => {
            const title =
                task.title ??
                task.payload?.title ??
                "";

            const status =
                task.status ?? "";

            return (
                title.toLowerCase().includes(term) ||
                status.toLowerCase().includes(term)
            );
        });
    }, [tasks, search]);


    const lastSyncedText = useMemo(() => {
        if (!syncStatus?.last_synced_at) {
            return "Never synced";
        }

        return new Date(
            syncStatus.last_synced_at
        ).toLocaleString();
    }, [syncStatus]);


    const isLoading =
        syncLoading ||
        workspacesLoading ||
        dashboardLoading ||
        tasksLoading ||
        currentUserLoading;

 


    if (isLoading) {
        return (
            <>
                <AppSidebar
                    currentWorkspace={currentWorkspace}
                    workspaces={[]}
                    username={currentUser?.username ?? ""}
                    userRole={currentWorkspace?.role}
                    activePage="dashboard"
                    onWorkspaceSelect={() => {}}
                    onManageWorkspaces={() => {}}
                    onCreateWorkspace={() => {}}
                    onDashboard={() => {}}
                    onMembers={() => {}}
                    onIntegrations={() => {}}
                    onProfile={() => {}}
                    onSignOut={() => {}}
                />

                <main className="ml-72 flex flex-1 flex-col">
                    <DashboardTopBar
                        title="Dashboard"
                        lastSynced="Loading..."
                        search=""
                        setSearch={() => {}}
                    />

                    <DashboardSkeleton />
                </main>
            </>
        );
    }

    

    

    

    if (syncError) {
        return (
            <>
                <AppSidebar
                    currentWorkspace={currentWorkspace}
                    workspaces={workspaces}
                    username={currentUser?.username ?? ""}
                    userRole={currentWorkspace?.role}
                    activePage="dashboard"
                    onWorkspaceSelect={(id) =>
                        router.push(`/workspaces/${id}/dashboard`)
                    }
                    onManageWorkspaces={() =>
                        router.push("/workspaces")
                    }
                    onCreateWorkspace={() =>
                        router.push("/workspaces/create")
                    }
                    onDashboard={() =>
                        router.push(`/workspaces/${workspaceId}/dashboard`)
                    }
                    onMembers={() =>
                        router.push(`/workspaces/${workspaceId}/members`)
                    }
                    onIntegrations={() =>
                        router.push(`/workspaces/${workspaceId}/integrations`)
                    }
                    onProfile={() =>
                        router.push("/profile")
                    }
                    onSignOut={() => {
                        useAuthStore.getState().clearAccessToken();
                        router.replace("/sign-in");
                    }}
                />

                <main className="ml-72 flex min-h-screen items-center justify-center">
                    <Card className="w-full max-w-md">
                        <CardContent className="space-y-4 p-6">
                            <h2 className="text-lg font-semibold">
                                Unable to load dashboard
                            </h2>

                            <p className="text-sm text-muted-foreground">
                                {(error as Error).message}
                            </p>
                        </CardContent>
                    </Card>
                </main>
            </>
        );
    }

    return (
        <main className="ml-72 flex flex-1 flex-col">
            <AppSidebar
                currentWorkspace={currentWorkspace}
                workspaces={workspaces}
                username={currentUser?.username ?? ""}
                userRole={currentWorkspace?.role}
                activePage="dashboard"
                onWorkspaceSelect={(id) =>
                    router.push(`/workspaces/${id}/dashboard`)
                }
                onManageWorkspaces={() =>
                    router.push("/workspaces")
                }
                onCreateWorkspace={() =>
                    router.push("/workspaces/create")
                }
                onDashboard={() =>
                    router.push(`/workspaces/${workspaceId}/dashboard`)
                }
                onMembers={() =>
                    router.push(`/workspaces/${workspaceId}/members`)
                }
                onIntegrations={() =>
                    router.push(`/workspaces/${workspaceId}/integrations`)
                }
                onProfile={() =>
                    router.push("/profile")
                }
                onSignOut={() => {
                    useAuthStore.getState().clearAccessToken();
                    router.replace("/sign-in");
                }}
            />

            <section className="flex flex-1 flex-col">
                <DashboardTopBar
                    title="Dashboard"
                    lastSynced={lastSyncedText}
                    search={search}
                    setSearch={setSearch}
                />

                <div className="space-y-8 p-8">

                    <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
                        {[
                            {
                                title: "Open Tasks",
                                value: dashboard?.by_status.TODO,
                                subtitle: "Across Jira & Notion",
                                icon: ListTodo,
                            },
                            {
                                title: "Completed",
                                value: dashboard?.by_status.DONE,
                                subtitle: "Latest sync",
                                icon: CheckCircle2,
                            },
                            {
                                title: "In Progress",
                                value: dashboard?.by_status.IN_PROGRESS,
                                subtitle: "Currently active",
                                icon: Clock3,
                            },
                            {
                                title: "Team Members",
                                value: currentWorkspace?.member_count,
                                subtitle: "Workspace users",
                                icon: Users,
                            },
                        ].map((stat) => (
                            <StatCard
                                key={stat.title}
                                title={stat.title}
                                value={stat.value ?? 0}
                                subtitle={stat.subtitle}
                                icon={stat.icon}
                            />
                        ))}
                    </div>

                    <div className="grid gap-8 xl:grid-cols-[2fr_1fr]">

                        <RecentTasksTable
                            tasks={filteredTasks.map((task) => ({
                                id: task.id,
                                title:
                                    task.title ??
                                    task.payload?.title ??
                                    "Untitled Task",
                                status: task.status ?? "TODO",
                            }))}
                        />

                        <div className="space-y-8">

                            <SyncStatusCard
                                lastSynced={lastSyncedText}
                                loading={syncMutation.isPending}
                                onSync={() =>
                                    syncMutation.mutate()
                                }
                            />

                            <AISummaryCard
                                summary={summary}
                                email={emailAddress}
                                setEmail={setEmailAddress}
                                generateLoading={summaryMutation.isPending}
                                generateError={summaryMutation.error?.message}
                                generateSuccess={summaryMutation.isSuccess}
                                emailLoading={emailMutation.isPending}
                                emailError={emailMutation.error?.message}
                                emailSuccess={emailMutation.isSuccess}
                                onGenerate={() => summaryMutation.mutate()}
                                onEmailMe={() => emailMutation.mutate(null)}
                                onEmailOther={() =>
                                    emailMutation.mutate(emailAddress)
                                }
                            />

                        </div>

                    </div>

                </div>
            </section>
        </main>
    );
}
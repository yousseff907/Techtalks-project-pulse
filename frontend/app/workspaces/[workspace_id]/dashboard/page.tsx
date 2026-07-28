"use client";

import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  Calendar,
  FileText,
  Inbox,
  LayoutGrid,
  ListChecks,
  RefreshCw,
  Settings,
  Users,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/lib/auth-store";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface TaskPayload {
  id?: string;
  key?: string;
  title?: string;
  description?: string | null;
  status?: string | null;
  priority?: string | null;
  assignee?: string | null;
  reporter?: string | null;
  project?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  due_date?: string | null;
  tags?: string[];
}

interface WorkspaceTask {
  id: number;
  integration_id: number;
  type: string;
  source: string;
  title: string | null;
  status: string | null;
  payload: TaskPayload | null;
  fetched_at: string;
}

interface WorkspaceDetails {
  id: number;
  name: string;
  member_count: number;
}

interface DashboardSummary {
  total_tasks: number;
  by_status: Record<string, number>;
  by_source: Record<string, { total?: number }>;
  completion_rate: number;
  workload: Record<string, number>;
}

interface SyncStatus {
  last_synced_at: string | null;
}

const STATUS_LABELS: Record<string, string> = {
  TODO: "To Do",
  IN_PROGRESS: "In Progress",
  DONE: "Done",
};

const STATUS_BADGE_CLASSES: Record<string, string> = {
  TODO: "bg-slate-100 text-slate-700",
  IN_PROGRESS: "bg-amber-100 text-amber-700",
  DONE: "bg-green-100 text-green-700",
};

const SOURCE_BADGE_CLASSES: Record<string, string> = {
  jira: "bg-blue-100 text-blue-700",
  notion: "bg-neutral-200 text-neutral-800",
};

// ---------------------------------------------------------------------------
// Data fetching
// ---------------------------------------------------------------------------

function authHeaders(token: string | null) {
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

async function fetchJSON<T>(url: string, token: string | null): Promise<T> {
  const response = await fetch(url, { headers: authHeaders(token) });

  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.detail ?? "Request failed");
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Small presentational helpers
// ---------------------------------------------------------------------------

function getTaskTitle(task: WorkspaceTask): string {
  return task.title || task.payload?.title || "Untitled task";
}

function formatDate(value: string | null | undefined): string {
  if (!value) return "—";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";

  return parsed.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function StatusBadge({ status }: { status: string | null }) {
  if (!status) {
    return (
      <span className="inline-flex rounded-full bg-muted px-2.5 py-1 text-xs font-semibold text-muted-foreground">
        No status
      </span>
    );
  }

  return (
    <span
      className={cn(
        "inline-flex rounded-full px-2.5 py-1 text-xs font-semibold",
        STATUS_BADGE_CLASSES[status] ?? "bg-muted text-muted-foreground"
      )}
    >
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

function SourceBadge({ source }: { source: string }) {
  const normalized = source.toLowerCase();
  const Icon = normalized === "notion" ? FileText : LayoutGrid;
  const label =
    normalized === "jira" ? "Jira" : normalized === "notion" ? "Notion" : source;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold",
        SOURCE_BADGE_CLASSES[normalized] ?? "bg-muted text-muted-foreground"
      )}
    >
      <Icon className="size-3.5" />
      {label}
    </span>
  );
}

const RECENT_TASKS_LIMIT = 8;

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function WorkspaceDashboardPage() {
  const params = useParams();
  const workspaceId = params.workspace_id as string;
  const queryClient = useQueryClient();

  const accessToken = useAuthStore((state: any) => state.accessToken);
  const [syncMessage, setSyncMessage] = useState("");
  const [isSyncing, setIsSyncing] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_URL;

  const {
    data: workspace,
    isLoading: workspaceLoading,
    isError: workspaceError,
  } = useQuery({
    queryKey: ["workspace", workspaceId],
    queryFn: () =>
      fetchJSON<WorkspaceDetails>(`${apiBase}/workspaces/${workspaceId}`, accessToken),
    enabled: !!accessToken,
  });

  const {
    data: summary,
    isLoading: summaryLoading,
    isError: summaryError,
  } = useQuery({
    queryKey: ["workspace-dashboard", workspaceId],
    queryFn: () =>
      fetchJSON<DashboardSummary>(
        `${apiBase}/workspaces/${workspaceId}/dashboard`,
        accessToken
      ),
    enabled: !!accessToken,
  });

  const {
    data: tasks,
    isLoading: tasksLoading,
    isError: tasksError,
  } = useQuery({
    queryKey: ["workspace-tasks", workspaceId, "recent"],
    queryFn: () =>
      fetchJSON<WorkspaceTask[]>(
        `${apiBase}/workspaces/${workspaceId}/data?type=task`,
        accessToken
      ),
    enabled: !!accessToken,
  });

  const { data: syncStatus } = useQuery({
    queryKey: ["workspace-sync-status", workspaceId],
    queryFn: () =>
      fetchJSON<SyncStatus>(
        `${apiBase}/workspaces/${workspaceId}/sync/status`,
        accessToken
      ),
    enabled: !!accessToken,
    retry: false,
  });

  const recentTasks = useMemo(() => {
    return [...(tasks ?? [])]
      .sort(
        (a, b) => new Date(b.fetched_at).getTime() - new Date(a.fetched_at).getTime()
      )
      .slice(0, RECENT_TASKS_LIMIT);
  }, [tasks]);

  const handleSync = async () => {
    setIsSyncing(true);
    setSyncMessage("");

    try {
      const response = await fetch(`${apiBase}/workspaces/${workspaceId}/sync`, {
        method: "POST",
        headers: authHeaders(accessToken),
      });

      if (!response.ok) {
        const error = await response.json().catch(() => null);
        throw new Error(error?.detail ?? "Failed to start sync");
      }

      setSyncMessage("Sync started — this can take a minute. Refresh shortly to see new data.");
      queryClient.invalidateQueries({ queryKey: ["workspace-sync-status", workspaceId] });
    } catch (err) {
      setSyncMessage(err instanceof Error ? err.message : "Failed to start sync.");
    } finally {
      setIsSyncing(false);
    }
  };

  if (workspaceLoading) {
    return <main className="mx-auto max-w-7xl p-8">Loading...</main>;
  }

  if (workspaceError) {
    return (
      <main className="mx-auto max-w-7xl p-8">
        <Card>
          <CardContent className="flex flex-col items-center justify-center gap-2 p-12">
            <AlertCircle className="size-6 text-destructive" />
            <p className="text-destructive">Failed to load workspace.</p>
          </CardContent>
        </Card>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-7xl p-8">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">{workspace?.name}</h1>

          <p className="text-muted-foreground">
            {workspace?.member_count} member{workspace?.member_count !== 1 ? "s" : ""}
            {syncStatus?.last_synced_at
              ? ` • Last synced ${new Date(syncStatus.last_synced_at).toLocaleString()}`
              : " • Never synced yet"}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleSync} disabled={isSyncing}>
            <RefreshCw className={cn("size-3.5", isSyncing && "animate-spin")} />
            {isSyncing ? "Syncing..." : "Sync Now"}
          </Button>

          <Link href={`/workspaces/${workspaceId}/tasks`}>
            <Button variant="outline" size="sm">
              <ListChecks className="size-3.5" />
              All Tasks
            </Button>
          </Link>

          <Link href={`/workspaces/${workspaceId}/members`}>
            <Button variant="outline" size="sm">
              <Users className="size-3.5" />
              Members
            </Button>
          </Link>

          <Link href={`/workspaces/${workspaceId}/integrations`}>
            <Button variant="outline" size="sm">
              <Settings className="size-3.5" />
              Integrations
            </Button>
          </Link>
        </div>
      </div>

      {syncMessage && (
        <p className="mt-3 text-sm text-muted-foreground">{syncMessage}</p>
      )}

      {summaryError && (
        <p className="mt-6 text-sm text-destructive">
          Failed to load dashboard summary.
        </p>
      )}

      {!summaryLoading && summary && (
        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground">Total Tasks</p>
              <p className="mt-1 text-2xl font-bold">{summary.total_tasks}</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground">Completion Rate</p>
              <p className="mt-1 text-2xl font-bold">{summary.completion_rate}%</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground">By Status</p>
              <div className="mt-2 space-y-1.5">
                {Object.entries(summary.by_status).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between">
                    <StatusBadge status={status} />
                    <span className="text-sm font-semibold">{String(count)}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <p className="text-sm text-muted-foreground">By Source</p>
              <div className="mt-2 space-y-1.5">
                {Object.entries(summary.by_source).map(([source, counts]) => (
                  <div key={source} className="flex items-center justify-between">
                      <SourceBadge source={source} />
                    <span className="text-sm font-semibold">{(counts as any)?.total ?? 0}</span>
                  </div>
                ))}
                {Object.keys(summary.by_source).length === 0 && (
                  <p className="text-sm text-muted-foreground">No synced data yet.</p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      <div className="mt-8 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Recent Tasks</h2>
        <Link
          href={`/workspaces/${workspaceId}/tasks`}
          className="text-sm text-primary hover:underline"
        >
          View all tasks →
        </Link>
      </div>

      {tasksLoading && (
        <p className="mt-4 text-sm text-muted-foreground">Loading tasks...</p>
      )}

      {tasksError && (
        <p className="mt-4 text-sm text-destructive">Failed to load tasks.</p>
      )}

      {!tasksLoading && !tasksError && recentTasks.length === 0 && (
        <Card className="mt-4">
          <CardContent className="flex flex-col items-center justify-center gap-2 py-16">
            <Inbox className="size-8 text-muted-foreground" />
            <h3 className="text-lg font-semibold">No tasks yet</h3>
            <p className="max-w-sm text-center text-muted-foreground">
              Tasks will show up here once a sync has run for this workspace&apos;s
              Jira or Notion integration.
            </p>
          </CardContent>
        </Card>
      )}

      {recentTasks.length > 0 && (
        <Card className="mt-4 overflow-hidden p-0">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead className="bg-muted/60">
                  <tr className="border-b">
                    <th className="px-6 py-4 text-left text-sm font-semibold">Task</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold">Source</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold">
                      Assignee
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold">
                      Priority
                    </th>
                    <th className="px-6 py-4 text-left text-sm font-semibold">Status</th>
                    <th className="px-6 py-4 text-left text-sm font-semibold">
                      Due date
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {recentTasks.map((task) => (
                    <tr key={task.id} className="border-b transition-colors hover:bg-muted/30">
                      <td className="max-w-xs truncate px-6 py-4 font-medium" title={getTaskTitle(task)}>
                        {getTaskTitle(task)}
                      </td>
                      <td className="px-6 py-4">
                        <SourceBadge source={task.source} />
                      </td>
                      <td className="px-6 py-4 text-sm">
                        {task.payload?.assignee || (
                          <span className="italic text-muted-foreground">Unassigned</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-sm text-muted-foreground">
                        {task.payload?.priority || "—"}
                      </td>
                      <td className="px-6 py-4">
                        <StatusBadge status={task.status} />
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                          <Calendar className="size-3.5" />
                          {formatDate(task.payload?.due_date)}
                        </div>
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
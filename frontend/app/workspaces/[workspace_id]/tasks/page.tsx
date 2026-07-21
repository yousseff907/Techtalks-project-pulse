"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowLeft,
  Calendar,
  FileText,
  Inbox,
  LayoutGrid,
  Loader2,
  Search,
  User,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
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

interface TaskFilters {
  source: string;
  status: string;
  search: string;
}

const SOURCE_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All sources" },
  { value: "jira", label: "Jira" },
  { value: "notion", label: "Notion" },
];

const STATUS_OPTIONS: { value: string; label: string }[] = [
  { value: "", label: "All statuses" },
  { value: "TODO", label: "To Do" },
  { value: "IN_PROGRESS", label: "In Progress" },
  { value: "DONE", label: "Done" },
];

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

async function fetchWorkspaceTasks(
  workspaceId: string,
  token: string | null,
  filters: TaskFilters
): Promise<WorkspaceTask[]> {
  const params = new URLSearchParams({ type: "task" });

  if (filters.source) params.set("source", filters.source);
  if (filters.status) params.set("status", filters.status);
  if (filters.search) params.set("search", filters.search);

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/workspaces/${workspaceId}/data?${params.toString()}`,
    { headers: authHeaders(token) }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => null);

    throw new Error(
      error?.detail ?? "Failed to fetch workspace tasks"
    );
  }

  return response.json();
}

// ---------------------------------------------------------------------------
// Small presentational helpers
// ---------------------------------------------------------------------------

function getTaskTitle(task: WorkspaceTask): string {
  return task.title || task.payload?.title || "Untitled task";
}

function getExternalKey(task: WorkspaceTask): string {
  const key = task.payload?.key;
  if (key) return key;

  const id = task.payload?.id;
  if (id) return id.length > 10 ? `${id.slice(0, 8)}…` : id;

  return `#${task.id}`;
}

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);

  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();

  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

function formatDueDate(dueDate: string | null | undefined): string {
  if (!dueDate) return "No due date";

  const parsed = new Date(dueDate);
  if (Number.isNaN(parsed.getTime())) return "No due date";

  return parsed.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function isOverdue(
  dueDate: string | null | undefined,
  status: string | null
): boolean {
  if (!dueDate || status === "DONE") return false;

  const parsed = new Date(dueDate);
  if (Number.isNaN(parsed.getTime())) return false;

  return parsed.getTime() < Date.now();
}

function SourceBadge({ source }: { source: string }) {
  const normalized = source.toLowerCase();
  const Icon = normalized === "notion" ? FileText : LayoutGrid;
  const label =
    normalized === "jira"
      ? "Jira"
      : normalized === "notion"
      ? "Notion"
      : source;

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

function AssigneeCell({ assignee }: { assignee: string | null | undefined }) {
  if (!assignee) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground">
        <div className="flex size-7 items-center justify-center rounded-full bg-muted">
          <User className="size-3.5" />
        </div>
        <span className="text-sm italic">Unassigned</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <div className="flex size-7 items-center justify-center rounded-full bg-primary/10 text-xs font-semibold text-primary">
        {getInitials(assignee)}
      </div>
      <span className="text-sm">{assignee}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function TasksPage() {
  const params = useParams();
  const workspaceId = params.workspace_id as string;

  const accessToken = useAuthStore((state: any) => state.accessToken);

  const [sourceFilter, setSourceFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // Debounce free-text search so we're not firing a request on every
  // keystroke; source/status filters apply immediately since they're
  // discrete selections.
  useEffect(() => {
    const handle = setTimeout(() => {
      setDebouncedSearch(searchInput.trim());
    }, 300);

    return () => clearTimeout(handle);
  }, [searchInput]);

  const filters: TaskFilters = {
    source: sourceFilter,
    status: statusFilter,
    search: debouncedSearch,
  };

  const {
    data: tasks = [],
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ["workspace-tasks", workspaceId, filters],
    queryFn: () =>
      fetchWorkspaceTasks(workspaceId, accessToken, filters),
    enabled: !!accessToken,
  });

  const hasActiveFilters =
    !!sourceFilter || !!statusFilter || !!searchInput;

  const clearFilters = () => {
    setSourceFilter("");
    setStatusFilter("");
    setSearchInput("");
  };

  const sortedTasks = useMemo(() => {
    return [...tasks].sort((a, b) =>
      getTaskTitle(a).localeCompare(getTaskTitle(b))
    );
  }, [tasks]);

  return (
    <main className="mx-auto max-w-7xl p-8">
      <Link
        href={`/workspaces/${workspaceId}`}
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="size-3.5" />
        Back to workspace
      </Link>

      <div className="mt-4 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold">All Tasks</h1>

          <p className="text-muted-foreground">
            Every task synced from your connected Jira and Notion
            workspaces.
          </p>
        </div>

        <div className="text-sm text-muted-foreground">
          {sortedTasks.length} task
          {sortedTasks.length !== 1 ? "s" : ""}
        </div>
      </div>

      <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground" />

          <Input
            className="border border-border pl-8 shadow-sm"
            placeholder="Search tasks by title..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>

        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm shadow-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          {SOURCE_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="h-8 rounded-lg border border-input bg-transparent px-2.5 text-sm shadow-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        {hasActiveFilters && (
          <Button variant="outline" size="sm" onClick={clearFilters}>
            Clear filters
          </Button>
        )}
      </div>

      {isLoading && (
        <Card className="mt-6">
          <CardContent className="flex items-center justify-center gap-2 p-12 text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            <p>Loading tasks...</p>
          </CardContent>
        </Card>
      )}

      {isError && (
        <Card className="mt-6">
          <CardContent className="flex flex-col items-center justify-center gap-2 p-12">
            <AlertCircle className="size-6 text-destructive" />

            <p className="text-destructive">
              {error instanceof Error
                ? error.message
                : "Failed to load tasks."}
            </p>
          </CardContent>
        </Card>
      )}

      {!isLoading && !isError && sortedTasks.length === 0 && (
        <Card className="mt-6">
          <CardContent className="flex flex-col items-center justify-center gap-2 py-16">
            <Inbox className="size-8 text-muted-foreground" />

            <h2 className="text-lg font-semibold">
              {hasActiveFilters ? "No matching tasks" : "No tasks yet"}
            </h2>

            <p className="max-w-sm text-center text-muted-foreground">
              {hasActiveFilters
                ? "Try adjusting or clearing your filters."
                : "Tasks will show up here once a sync has run for this workspace's Jira or Notion integration."}
            </p>

            {hasActiveFilters && (
              <Button variant="outline" size="sm" onClick={clearFilters}>
                Clear filters
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {!isLoading && !isError && sortedTasks.length > 0 && (
        <Card className="mt-6 overflow-hidden p-0">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead className="bg-muted/60">
                  <tr className="border-b">
                    <th className="px-6 py-4 text-left text-sm font-semibold">
                      Task
                    </th>

                    <th className="px-6 py-4 text-left text-sm font-semibold">
                      Source
                    </th>

                    <th className="px-6 py-4 text-left text-sm font-semibold">
                      Assignee
                    </th>

                    <th className="px-6 py-4 text-left text-sm font-semibold">
                      Status
                    </th>

                    <th className="px-6 py-4 text-left text-sm font-semibold">
                      Due date
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {sortedTasks.map((task) => {
                    const dueDate = task.payload?.due_date;
                    const overdue = isOverdue(dueDate, task.status);

                    return (
                      <tr
                        key={task.id}
                        className="border-b transition-colors hover:bg-muted/30"
                      >
                        <td className="px-6 py-5 align-middle">
                          <p className="font-medium">
                            {getTaskTitle(task)}
                          </p>

                          <p className="text-sm text-muted-foreground">
                            {getExternalKey(task)}
                          </p>
                        </td>

                        <td className="px-6 py-5 align-middle">
                          <SourceBadge source={task.source} />
                        </td>

                        <td className="px-6 py-5 align-middle">
                          <AssigneeCell
                            assignee={task.payload?.assignee}
                          />
                        </td>

                        <td className="px-6 py-5 align-middle">
                          <StatusBadge status={task.status} />
                        </td>

                        <td className="px-6 py-5 align-middle">
                          <div
                            className={cn(
                              "flex items-center gap-1.5 text-sm",
                              dueDate
                                ? overdue
                                  ? "font-medium text-destructive"
                                  : "text-foreground"
                                : "text-muted-foreground"
                            )}
                          >
                            <Calendar className="size-3.5" />
                            {formatDueDate(dueDate)}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </main>
  );
}
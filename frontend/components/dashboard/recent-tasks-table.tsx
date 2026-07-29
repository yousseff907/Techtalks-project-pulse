import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Calendar } from "lucide-react";

// Shape this component actually needs, built from the normalized
// WorkspaceData payload that both gather_and_store_jira_tasks and
// gather_and_store_notion_tasks produce. Both sync jobs write the same
// keys (status, assignee, priority, due_date, ...), so this table never
// needs to branch on `source` to know where to find a field - only to
// render the small "Jira"/"Notion" pill.
interface Task {
    id: number;
    title: string;
    status: string;
    source: string;
    assignee?: string | null;
    priority?: string | null;
    due_date?: string | null;
}

interface RecentTasksTableProps {
    tasks: Task[];
}

// Normalizes any status spelling ("IN_PROGRESS", "In Progress", "in progress")
// down to a single key so the badge coloring works regardless of whether it
// came from Jira's normalize_jira_status, Notion's _normalize_status, or an
// unrecognized status that either sync passed through unchanged.
function statusKey(status: string): string {
    return status.trim().toUpperCase().replace(/[\s-]+/g, "_");
}

const STATUS_LABELS: Record<string, string> = {
    TODO: "To Do",
    TO_DO: "To Do",
    OPEN: "To Do",
    BACKLOG: "To Do",
    IN_PROGRESS: "In Progress",
    IN_REVIEW: "In Review",
    REVIEW: "In Review",
    DONE: "Done",
    COMPLETED: "Done",
    BLOCKED: "Blocked",
};

function StatusBadge({ status }: { status: string }) {
    if (!status) {
        return (
            <Badge
                variant="secondary"
                className="inline-flex bg-slate-100 text-slate-700 hover:bg-slate-100"
            >
                No status
            </Badge>
        );
    }

    const key = statusKey(status);
    const label = STATUS_LABELS[key] ?? status;

    switch (key) {
        case "DONE":
        case "COMPLETED":
            return (
                <Badge className="inline-flex bg-green-100 text-green-700 hover:bg-green-100">
                    {label}
                </Badge>
            );

        case "IN_PROGRESS":
            return (
                <Badge className="inline-flex bg-blue-100 text-blue-700 hover:bg-blue-100">
                    {label}
                </Badge>
            );

        case "IN_REVIEW":
        case "REVIEW":
            return (
                <Badge className="inline-flex bg-amber-100 text-amber-700 hover:bg-amber-100">
                    {label}
                </Badge>
            );

        case "BLOCKED":
            return (
                <Badge className="inline-flex bg-red-100 text-red-700 hover:bg-red-100">
                    {label}
                </Badge>
            );

        case "TODO":
        case "TO_DO":
        case "BACKLOG":
        case "OPEN":
        default:
            return (
                <Badge
                    variant="secondary"
                    className="inline-flex bg-slate-100 text-slate-700 hover:bg-slate-100"
                >
                    {label}
                </Badge>
            );
    }
}

function SourceBadge({ source }: { source: string }) {
    const normalized = (source ?? "").toLowerCase();

    if (normalized === "jira") {
        return (
            <Badge className="inline-flex bg-blue-50 text-blue-700 hover:bg-blue-50">
                Jira
            </Badge>
        );
    }

    if (normalized === "notion") {
        return (
            <Badge className="inline-flex bg-neutral-200 text-neutral-800 hover:bg-neutral-200">
                Notion
            </Badge>
        );
    }

    return (
        <Badge variant="secondary" className="inline-flex">
            {source || "Unknown"}
        </Badge>
    );
}

function formatDueDate(value?: string | null): string {
    if (!value) return "No due date";

    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return "No due date";

    return parsed.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
    });
}

export function RecentTasksTable({
    tasks,
}: RecentTasksTableProps) {
    return (
        <Card>
            <CardHeader className="pb-3">
                <CardTitle>
                    Recent Tasks
                </CardTitle>
            </CardHeader>

            <CardContent className="pt-0">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="border-b">
                            <tr>
                                <th className="pb-3 text-left text-sm font-medium text-muted-foreground">
                                    Task
                                </th>

                                <th className="w-24 pb-3 text-left text-sm font-medium text-muted-foreground">
                                    Source
                                </th>

                                <th className="w-40 pb-3 text-left text-sm font-medium text-muted-foreground">
                                    Assignee
                                </th>

                                <th className="w-28 pb-3 text-left text-sm font-medium text-muted-foreground">
                                    Priority
                                </th>

                                <th className="w-36 pb-3 text-center text-sm font-medium text-muted-foreground">
                                    Status
                                </th>

                                <th className="w-36 pb-3 text-left text-sm font-medium text-muted-foreground">
                                    Due date
                                </th>
                            </tr>
                        </thead>

                        <tbody>
                            {tasks.map((task) => (
                                <tr
                                    key={task.id}
                                    className="border-b transition-colors hover:bg-muted/20 last:border-0"
                                >
                                    <td className="py-4 font-medium">
                                        {task.title}
                                    </td>

                                    <td className="py-4 align-middle">
                                        <SourceBadge source={task.source} />
                                    </td>

                                    <td className="py-4 align-middle text-sm">
                                        {task.assignee ? (
                                            task.assignee
                                        ) : (
                                            <span className="italic text-muted-foreground">
                                                Unassigned
                                            </span>
                                        )}
                                    </td>

                                    <td className="py-4 align-middle text-sm">
                                        {task.priority || (
                                            <span className="text-muted-foreground">—</span>
                                        )}
                                    </td>

                                    <td className="py-4 text-center align-middle">
                                        <StatusBadge
                                            status={task.status}
                                        />
                                    </td>

                                    <td className="py-4 align-middle text-sm">
                                        <div className="flex items-center gap-1.5 text-muted-foreground">
                                            <Calendar className="h-3.5 w-3.5" />
                                            {formatDueDate(task.due_date)}
                                        </div>
                                    </td>
                                </tr>
                            ))}

                            {tasks.length === 0 && (
                                <tr>
                                    <td
                                        colSpan={6}
                                        className="py-10 text-center text-sm text-muted-foreground"
                                    >
                                        <p>No tasks found.</p>

                                        <p className="mt-1">
                                            Tasks from Jira and Notion will appear
                                            here after your first sync.
                                        </p>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </CardContent>
        </Card>
    );
}
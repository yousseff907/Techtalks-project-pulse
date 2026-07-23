import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface Task {
    id: number;
    title: string;
    status: string;
}

interface RecentTasksTableProps {
    tasks: Task[];
}

function StatusBadge({
    status,
}: {
    status: string;
}) {
    switch (status.toLowerCase()) {
        case "done":
        case "completed":
            return (
                <Badge className="inline-flex bg-green-100 text-green-700 hover:bg-green-100">
                    {status}
                </Badge>
            );

        case "in progress":
            return (
                <Badge className="inline-flex bg-blue-100 text-blue-700 hover:bg-blue-100">
                    {status}
                </Badge>
            );

        case "in review":
        case "review":
            return (
                <Badge className="inline-flex bg-amber-100 text-amber-700 hover:bg-amber-100">
                    {status}
                </Badge>
            );

        case "blocked":
            return (
                <Badge className="inline-flex bg-red-100 text-red-700 hover:bg-red-100">
                    {status}
                </Badge>
            );

        case "todo":
        case "to do":
        case "backlog":
        case "open":
        default:
            return (
                <Badge
                    variant="secondary"
                    className="inline-flex bg-slate-100 text-slate-700 hover:bg-slate-100"
                >
                    {status}
                </Badge>
            );
    }
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
                <table className="w-full">
                    <thead className="border-b">
                        <tr>
                            <th className="pb-3 text-left text-sm font-medium text-muted-foreground">
                                Task
                            </th>

                            <th className="w-44 pb-3 text-center text-sm font-medium text-muted-foreground">
                                Status
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

                                <td className="py-4 text-center align-middle">
                                    <StatusBadge
                                        status={task.status}
                                    />
                                </td>
                            </tr>
                        ))}

                        {tasks.length === 0 && (
                            <tr>
                                <td
                                    colSpan={2}
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
            </CardContent>
        </Card>
    );
}
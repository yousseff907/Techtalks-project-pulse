import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";

interface SyncStatusCardProps {
    lastSynced: string;
    loading: boolean;
    onSync: () => void;
}

export function SyncStatusCard({
    lastSynced,
    loading,
    onSync,
}: SyncStatusCardProps) {
    return (
        <Card>
            <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>
                    Sync Status
                </CardTitle>

                <Button
                    size="icon"
                    variant="outline"
                    onClick={onSync}
                    disabled={loading}
                >
                    <RefreshCw
                        className={`h-4 w-4 ${
                            loading ? "animate-spin" : ""
                        }`}
                    />
                </Button>
            </CardHeader>

            <CardContent>
                <p className="text-sm text-muted-foreground">
                    Last synced
                </p>

                <p className="mt-2 text-lg font-semibold">
                    {lastSynced}
                </p>
            </CardContent>
        </Card>
    );
}
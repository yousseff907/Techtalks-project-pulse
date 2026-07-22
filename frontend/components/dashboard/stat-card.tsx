import { Card, CardContent } from "@/components/ui/card";
import { LucideIcon } from "lucide-react";

interface StatCardProps {
    title: string;
    value: number;
    subtitle?: string;
    icon?: LucideIcon;
}

export function StatCard({
    title,
    value,
    subtitle,
    icon: Icon,
}: StatCardProps) {
    return (
        <Card>
            <CardContent className="p-6">
                <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-muted-foreground">
                        {title}
                    </p>

                    {Icon && (
                        <Icon className="h-5 w-5 text-muted-foreground" />
                    )}
                </div>

                <h2 className="mt-2 text-3xl font-bold tracking-tight">
                    {value}
                </h2>

                {subtitle && (
                    <p className="mt-1 text-sm text-muted-foreground">
                        {subtitle}
                    </p>
                )}
            </CardContent>
        </Card>
    );
}
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function DashboardSkeleton() {
    return (
        <div className="space-y-8 p-8">

            <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
                {Array.from({ length: 4 }).map((_, i) => (
                    <Card key={i}>
                        <CardContent className="space-y-3 p-6">
                            <Skeleton className="h-4 w-24" />
                            <Skeleton className="h-9 w-20" />
                            <Skeleton className="h-3 w-32" />
                        </CardContent>
                    </Card>
                ))}
            </div>

            <div className="grid gap-8 xl:grid-cols-[2fr_1fr]">

                <Card>
                    <CardContent className="space-y-4 p-6">
                        <Skeleton className="h-6 w-40" />

                        {Array.from({ length: 6 }).map((_, i) => (
                            <div
                                key={i}
                                className="flex justify-between"
                            >
                                <Skeleton className="h-5 w-56" />
                                <Skeleton className="h-5 w-20" />
                            </div>
                        ))}
                    </CardContent>
                </Card>

                <div className="space-y-8">

                    <Card>
                        <CardContent className="space-y-4 p-6">
                            <Skeleton className="h-6 w-32" />
                            <Skeleton className="h-5 w-40" />
                        </CardContent>
                    </Card>

                    <Card>
                        <CardContent className="space-y-4 p-6">
                            <Skeleton className="h-10 w-full" />

                            <div className="space-y-2">
                                <Skeleton className="h-4 w-full" />
                                <Skeleton className="h-4 w-5/6" />
                                <Skeleton className="h-4 w-4/6" />
                                <Skeleton className="h-4 w-3/6" />
                            </div>

                            <Skeleton className="h-10 w-full" />

                            <div className="flex gap-2">
                                <Skeleton className="h-10 flex-1" />
                                <Skeleton className="h-10 w-20" />
                            </div>
                        </CardContent>
                    </Card>

                </div>

            </div>

        </div>
    );
}
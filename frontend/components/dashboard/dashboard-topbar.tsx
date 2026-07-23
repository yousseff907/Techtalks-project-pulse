"use client";

import { Bell, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface DashboardTopBarProps {
    title: string;
    lastSynced: string;
    search: string;
    setSearch: (value: string) => void;
}

export function DashboardTopBar({
    title,
    lastSynced,
    search,
    setSearch,
}: DashboardTopBarProps) {
    return (
        <header className="flex items-center border-b bg-background px-8 py-5">
            <div className="flex flex-1 flex-col">
                <h1 className="text-3xl font-bold tracking-tight">
                    {title}
                </h1>

                <p className="mt-1 text-sm text-muted-foreground">
                    Last synced {lastSynced}
                </p>
            </div>

            <div className="flex flex-1 justify-center">
                <div className="relative w-full max-w-md">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />

                    <Input
                        value={search}
                        onChange={(e) =>
                            setSearch(e.target.value)
                        }
                        placeholder="Search tasks..."
                        className="w-lg rounded-xl border border-border/60 bg-background pl-10 shadow-sm transition-all hover:border-border focus-visible:border-primary focus-visible:ring-2 focus-visible:ring-primary/20"
                        />
                </div>
            </div>

            <div className="flex flex-1 justify-end">
                <Button
                    variant="outline"
                    size="icon"
                >
                    <Bell className="h-5 w-5" />
                </Button>
            </div>
        </header>
    );
}
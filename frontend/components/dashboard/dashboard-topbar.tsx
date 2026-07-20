"use client";

import { Bell, RefreshCw, Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface DashboardTopBarProps {
    title: string;
    lastSynced: string;
    syncLoading: boolean;
    search: string;
    setSearch: (value: string) => void;
    onSync: () => void;
}

export function DashboardTopBar({
    title,
    lastSynced,
    syncLoading,
    search,
    setSearch,
    onSync,
}: DashboardTopBarProps) {
    return (
        <header className="flex items-center justify-between border-b bg-background px-8 py-5">
            <div>
                <h1 className="text-3xl font-bold tracking-tight">
                    {title}
                </h1>

                <p className="mt-1 text-sm text-muted-foreground">
                    Last synced {lastSynced}
                </p>
            </div>

            <div className="flex items-center gap-4">

                <Button
                    onClick={onSync}
                    disabled={syncLoading}
                    className="gap-2"
                >
                    <RefreshCw
                        className={`h-4 w-4 ${
                            syncLoading
                                ? "animate-spin"
                                : ""
                        }`}
                    />

                    {syncLoading
                        ? "Syncing..."
                        : "Sync Now"}
                </Button>

                <div className="relative">
                    <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />

                    <Input
                        value={search}
                        onChange={(e) =>
                            setSearch(e.target.value)
                        }
                        placeholder="Search tasks..."
                        className="w-72 border-2 border-muted-foreground/20 bg-background pl-10 shadow-sm focus-visible:border-primary"
                    />
                </div>

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
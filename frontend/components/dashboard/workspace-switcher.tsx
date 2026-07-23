"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown } from "lucide-react";

interface Workspace {
    id: number;
    name: string;
    role: string;
    member_count: number;
}

interface WorkspaceSwitcherProps {
    currentWorkspace: Workspace;
    workspaces: Workspace[];

    onWorkspaceSelect: (workspaceId: number) => void;
    onCreateWorkspace: () => void;
}

export function WorkspaceSwitcher({
    currentWorkspace,
    workspaces,
    onWorkspaceSelect,
    onCreateWorkspace,
}: WorkspaceSwitcherProps) {
    const [open, setOpen] = useState(false);

    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (
                containerRef.current &&
                !containerRef.current.contains(event.target as Node)
            ) {
                setOpen(false);
            }
        }

        document.addEventListener("mousedown", handleClickOutside);

        return () =>
            document.removeEventListener(
                "mousedown",
                handleClickOutside
            );
    }, []);

    return (
        <div
            ref={containerRef}
            className="relative"
        >
            <Button
                variant="outline"
                onClick={() => setOpen(!open)}
                className="h-auto w-full justify-between rounded-xl border px-4 py-4 shadow-sm transition-all hover:bg-muted"
            >
                <div className="text-left">
                    <p className="font-semibold">
                        {currentWorkspace.name}
                    </p>

                    <p className="text-xs text-muted-foreground">
                        {currentWorkspace.role} •{" "}
                        {currentWorkspace.member_count} members
                    </p>
                </div>

                <ChevronDown
                    className={`h-4 w-4 transition-transform duration-200 ${
                        open ? "rotate-180" : ""
                    }`}
                />
            </Button>

            {open && (
                <div className="absolute left-0 right-0 z-50 mt-3 rounded-xl border bg-background p-2 shadow-xl">

                    {workspaces.map((workspace) => (
                        <button
                            key={`${workspace.id}-${workspace.name}`}
                            onClick={() => {
                                setOpen(false);
                                onWorkspaceSelect(workspace.id);
                            }}
                            className={`mb-1 flex w-full flex-col rounded-lg px-3 py-3 text-left transition-colors hover:bg-muted ${
                                workspace.id === currentWorkspace.id
                                    ? "bg-primary/10 text-primary"
                                    : ""
                            }`}
                        >
                            <span className="font-medium">
                                {workspace.name}
                            </span>

                            <span className="text-xs text-muted-foreground">
                                {workspace.role}
                            </span>
                        </button>
                    ))}

                    <div className="my-2 border-t" />

                    <button
                        onClick={() => {
                            setOpen(false);
                            onCreateWorkspace();
                        }}
                        className="w-full rounded-lg px-3 py-3 text-left text-sm font-medium transition-colors hover:bg-muted"
                    >
                        Create or Join New Workspace
                    </button>

                </div>
            )}
        </div>
    );
}



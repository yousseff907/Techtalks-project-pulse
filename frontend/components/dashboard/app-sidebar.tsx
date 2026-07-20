"use client";

import { Button } from "@/components/ui/button";

import { WorkspaceSwitcher } from "./workspace-switcher";
import { ProfileSection } from "./profile-section";

import {
    LayoutDashboard,
    Users,
    Briefcase,
    Plug,
    LogOut,
} from "lucide-react";

interface Workspace {
    id: number;
    name: string;
    role: string;
    member_count: number;
}

interface AppSidebarProps {
    currentWorkspace: Workspace;
    workspaces: Workspace[];

    username: string;
    userRole: string;

    activePage:
        | "dashboard"
        | "members"
        | "integrations"
        | "workspaces";

    onWorkspaceSelect: (id: number) => void;
    onManageWorkspaces: () => void;
    onCreateWorkspace: () => void;

    onDashboard: () => void;
    onMembers: () => void;
    onIntegrations: () => void;
    onProfile: () => void;
    onSignOut: () => void;
}

export function AppSidebar({
    currentWorkspace,
    workspaces,

    username,
    activePage,
    userRole,

    onWorkspaceSelect,
    onManageWorkspaces,
    onCreateWorkspace,

    onDashboard,
    onMembers,
    onIntegrations,
    onProfile,
    onSignOut,
}: AppSidebarProps) {
    return (
        <aside className="fixed left-0 top-0 flex h-screen w-72 flex-col border-r bg-background px-4 py-5">

           
            <div>
                <h1 className="mb-6 text-2xl font-bold tracking-tight">
                    Project Pulse
                </h1>

                <WorkspaceSwitcher
                    currentWorkspace={currentWorkspace}
                    workspaces={workspaces}
                    onWorkspaceSelect={onWorkspaceSelect}
                    onCreateWorkspace={onCreateWorkspace}
                />
            </div>

            
            <div className="mt-5 border-b" />

            
            <nav className="mt-5 flex flex-1 flex-col gap-2">

                <Button
                    variant={
                        activePage === "dashboard"
                            ? "default"
                            : "ghost"
                    }
                    className={`h-12 w-full justify-start gap-3 rounded-xl px-4 transition-all duration-200 ${
                        activePage === "dashboard"
                            ? "shadow-sm font-semibold"
                            : ""
                    }`}
                    onClick={onDashboard}
                >
                    <LayoutDashboard className="h-5 w-5" />
                    Dashboard
                </Button>

                <Button
                    variant={
                        activePage === "members"
                            ? "default"
                            : "ghost"
                    }
                    className={`h-12 w-full justify-start gap-3 rounded-xl px-4 transition-all duration-200 ${
                        activePage === "members"
                            ? "shadow-sm font-semibold"
                            : ""
                    }`}
                    onClick={onMembers}
                >
                    <Users className="h-5 w-5" />
                    Team Directory
                </Button>

                <Button
                    variant={
                        activePage === "workspaces"
                            ? "default"
                            : "ghost"
                    }
                    className={`h-12 w-full justify-start gap-3 rounded-xl px-4 transition-all duration-200 ${
                        activePage === "workspaces"
                            ? "shadow-sm font-semibold"
                            : ""
                    }`}
                    onClick={onManageWorkspaces}
                >
                    <Briefcase className="h-5 w-5" />
                    Manage Workspaces
                </Button>

                <Button
                    variant={
                        activePage === "integrations"
                            ? "default"
                            : "ghost"
                    }
                    className={`h-12 w-full justify-start gap-3 rounded-xl px-4 transition-all duration-200 ${
                        activePage === "integrations"
                            ? "shadow-sm font-semibold"
                            : ""
                    }`}
                    onClick={onIntegrations}
                >
                    <Plug className="h-5 w-5" />
                    Integration Settings
                </Button>

            </nav>

            <div className="mt-auto border-t pt-5 pb-1">

                <ProfileSection
                    name={username}
                    role={userRole}
                    onClick={onProfile}
                />

                <Button
                    variant="ghost"
                    className="mt-3 h-11 w-full justify-start gap-3 rounded-xl px-4 text-muted-foreground transition-colors duration-200 hover:text-destructive"
                    onClick={onSignOut}
                >
                    <LogOut className="h-5 w-5" />
                    Sign out
                </Button>

            </div>
        </aside>
    );
}
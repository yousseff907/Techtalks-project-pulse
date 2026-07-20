"use client";

import { Button } from "@/components/ui/button";
import {
    ChevronRight,
    UserCircle,
} from "lucide-react";

interface ProfileSectionProps {
    name: string;
    role: string;
    onClick: () => void;
}

export function ProfileSection({
    name,
    role,
    onClick,
}: ProfileSectionProps) {
    return (
        <Button
            variant="ghost"
            onClick={onClick}
            className="h-auto w-full justify-between rounded-xl p-3 transition-colors hover:bg-muted"
        >
            <div className="flex items-center gap-3">
                <UserCircle className="h-11 w-11 text-muted-foreground" />

                <div className="text-left">
                    <p className="font-medium leading-none">
                        {name}
                    </p>

                    <p className="mt-1 text-xs text-muted-foreground">
                        {role}
                    </p>
                </div>
            </div>

            <ChevronRight className="h-4 w-4 text-muted-foreground" />
        </Button>
    );
}
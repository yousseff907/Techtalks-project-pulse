import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Sparkles } from "lucide-react";

interface AISummaryCardProps {
    summary: string;
    email: string;
    setEmail: (value: string) => void;

    generateLoading: boolean;
    generateError?: string;
    generateSuccess: boolean;

    emailLoading: boolean;
    emailError?: string;
    emailSuccess: boolean;

    onGenerate: () => void;
    onEmailMe: () => void;
    onEmailOther: () => void;
}

export function AISummaryCard({
    summary,
    email,
    setEmail,

    generateLoading,
    generateError,
    generateSuccess,

    emailLoading,
    emailError,
    emailSuccess,

    onGenerate,
    onEmailMe,
    onEmailOther,
}: AISummaryCardProps) {
    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5" />
                    AI Workspace Summary
                </CardTitle>
            </CardHeader>

            <CardContent className="space-y-6">
                <Button
                    onClick={onGenerate}
                    disabled={generateLoading}
                >
                    {generateLoading
                        ? "Generating..."
                        : summary
                            ? "Regenerate Summary"
                            : "Generate Latest Workspace Summary"}
                </Button>

                <div className="rounded-lg border bg-muted/30 p-4 min-h-40">

                    {generateLoading ? (
                        <p className="text-sm text-muted-foreground">
                            Generating workspace summary...
                        </p>
                    ) : summary ? (
                        <p className="whitespace-pre-wrap text-sm leading-6">
                            {summary}
                        </p>
                    ) : (
                        <p className="text-sm text-muted-foreground">
                            No summary has been generated yet.
                            Click <strong>Generate Latest Workspace Summary</strong> to
                            create one.
                        </p>
                    )}

                </div>

                {generateError && (
                    <p className="text-sm text-destructive">
                        {generateError}
                    </p>
                )}

                {generateSuccess && !generateLoading && (
                    <p className="text-sm text-green-600">
                        Workspace summary generated successfully.
                    </p>
                )}

                <div className="space-y-3">
                    <Button
                        variant="outline"
                        onClick={onEmailMe}
                        disabled={
                            !summary ||
                            emailLoading ||
                            generateLoading
                        }
                    >
                        Email to Me
                    </Button>

                    <div className="space-y-2">

                        <div className="flex gap-2">
                            <Input
                                placeholder="someone@example.com"
                                value={email}
                                onChange={(e) =>
                                    setEmail(e.target.value)
                                }
                                className="w-72 border border-border bg-background shadow-sm"
                            />

                            <Button
                                onClick={onEmailOther}
                                disabled={
                                    !summary ||
                                    emailLoading ||
                                    generateLoading ||
                                    !email.trim()
                                }
                            >
                                Email Other
                            </Button>
                        </div>

                        {emailError && (
                            <p className="text-sm text-destructive">
                                {emailError}
                            </p>
                        )}

                        {emailSuccess && !emailLoading && (
                            <p className="text-sm text-green-600">
                                Summary emailed successfully.
                            </p>
                        )}

                    </div>
                </div>
            </CardContent>
        </Card>
    );
}
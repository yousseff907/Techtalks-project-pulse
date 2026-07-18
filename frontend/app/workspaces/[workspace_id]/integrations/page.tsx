"use client";

import { useState } from "react";
import { useParams } from "next/navigation";

import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

import { useMutation, useQuery } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Label } from "@/components/ui/label";

import api from "@/lib/api";

import { jiraSchema, notionSchema } from "@/lib/validation";

type JiraFormValues = z.infer<typeof jiraSchema>;
type NotionFormValues = z.infer<typeof notionSchema>;

interface Workspace {
  role: string;
  jira_connected_at: string | null;
  notion_connected_at: string | null;
}

export default function IntegrationsPage() {
  const { workspace_id } = useParams();

  const [jiraError, setJiraError] = useState("");
  const [notionError, setNotionError] = useState("");

  const {
    data: workspace,
    refetch,
    isLoading,
    isError,
  } = useQuery({
    queryKey: ["workspace", workspace_id],
    queryFn: async () => {
      const { data } = await api.get(`/workspaces/${workspace_id}`);
      return data as Workspace;
    },
  });

  const jiraForm = useForm<JiraFormValues>({
    resolver: zodResolver(jiraSchema),
    defaultValues: {
      base_url: "",
      admin_email: "",
      api_key: "",
    },
  });

  const notionForm = useForm<NotionFormValues>({
    resolver: zodResolver(notionSchema),
    defaultValues: {
      api_key: "",
    },
  });

  const jiraMutation = useMutation({
    mutationFn: async (values: JiraFormValues) => {
      return api.patch(
        `/workspaces/${workspace_id}/integrations/jira`,
        values
      );
    },
    onSuccess: () => {
      setJiraError("");
      refetch();
      alert("Jira connected successfully.");
    },
    onError: (error: any) => {
      setJiraError(
        error?.response?.data?.detail ?? "Invalid Jira credentials"
      );
    },
  });

  const notionMutation = useMutation({
    mutationFn: async (values: NotionFormValues) => {
      return api.patch(
        `/workspaces/${workspace_id}/integrations/notion`,
        values
      );
    },
    onSuccess: () => {
      setNotionError("");
      refetch();
      alert("Notion connected successfully.");
    },
    onError: (error: any) => {
      setNotionError(
        error?.response?.data?.detail ?? "Invalid Notion credentials"
      );
    },
  });

  if (isLoading) {
    return <div className="p-10">Loading...</div>;
  }

  if (isError) {
    return (
      <div className="p-10 text-red-600">
        Failed to load workspace. Please try again.
      </div>
    );
  }

  const readOnly =
    workspace?.role !== "owner" && workspace?.role !== "admin";

  return (
    <div className="max-w-4xl mx-auto py-10 space-y-8">
      <h1 className="text-3xl font-bold">Workspace Integrations</h1>

      {readOnly && (
        <div className="rounded-md border border-red-300 bg-red-50 p-4 text-red-600">
          You don't have permission to edit integrations.
        </div>
      )}

      {/* Jira */}
      <Card>
        <CardHeader>
          <CardTitle>Jira</CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          <div>
            <p className="font-medium">Status</p>
            {workspace?.jira_connected_at ? (
              <span className="text-green-600">Connected</span>
            ) : (
              <span className="text-muted-foreground">Not Connected</span>
            )}
          </div>

          {workspace?.jira_connected_at && (
            <p className="text-sm text-muted-foreground">
              Connected at:{" "}
              {new Date(workspace.jira_connected_at).toLocaleString()}
            </p>
          )}

          <form
            className="space-y-4"
            onSubmit={jiraForm.handleSubmit((values) =>
              jiraMutation.mutate(values)
            )}
          >
            <div>
              <Label>Base URL</Label>
              <Input
                className="border border-border shadow-sm"
                placeholder="https://company.atlassian.net"
                disabled={readOnly}
                {...jiraForm.register("base_url")}
              />
              <p className="text-sm text-red-500">
                {jiraForm.formState.errors.base_url?.message}
              </p>
            </div>

            <div>
              <Label>Admin Email</Label>
              <Input
                className="border border-border shadow-sm"
                placeholder="admin@example.com"
                disabled={readOnly}
                {...jiraForm.register("admin_email")}
              />
              <p className="text-sm text-red-500">
                {jiraForm.formState.errors.admin_email?.message}
              </p>
            </div>

            <div>
              <Label>API Key</Label>
              <Input
                type="password"
                className="border border-border shadow-sm"
                placeholder="Enter Jira API token"
                disabled={readOnly}
                {...jiraForm.register("api_key")}
              />
              <p className="text-sm text-red-500">
                {jiraForm.formState.errors.api_key?.message}
              </p>
            </div>

            {jiraError && <p className="text-red-600">{jiraError}</p>}

            {!readOnly && (
              <Button type="submit" disabled={jiraMutation.isPending}>
                {jiraMutation.isPending ? "Saving..." : "Save Jira"}
              </Button>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Notion */}
      <Card>
        <CardHeader>
          <CardTitle>Notion</CardTitle>
        </CardHeader>

        <CardContent className="space-y-6">
          <div>
            <p className="font-medium">Status</p>
            {workspace?.notion_connected_at ? (
              <span className="text-green-600">Connected</span>
            ) : (
              <span className="text-muted-foreground">Not Connected</span>
            )}
          </div>

          {workspace?.notion_connected_at && (
            <p className="text-sm text-muted-foreground">
              Connected at:{" "}
              {new Date(workspace.notion_connected_at).toLocaleString()}
            </p>
          )}

          <form
            className="space-y-4"
            onSubmit={notionForm.handleSubmit((values) =>
              notionMutation.mutate(values)
            )}
          >
            <div>
              <Label>API Key</Label>
              <Input
                type="password"
                className="border border-border shadow-sm"
                placeholder="Enter Notion integration token"
                disabled={readOnly}
                {...notionForm.register("api_key")}
              />
              <p className="text-sm text-red-500">
                {notionForm.formState.errors.api_key?.message}
              </p>
            </div>

            {notionError && <p className="text-red-600">{notionError}</p>}

            {!readOnly && (
              <Button type="submit" disabled={notionMutation.isPending}>
                {notionMutation.isPending ? "Saving..." : "Save Notion"}
              </Button>
            )}
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
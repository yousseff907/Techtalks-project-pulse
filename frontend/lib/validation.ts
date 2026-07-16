import { z } from "zod";

export const jiraSchema = z.object({
  base_url: z.string().min(1),
  email: z.string().email(),
  api_token: z.string().min(1),
});

export const notionSchema = z.object({
  api_token: z.string().min(1),
});

export type JiraFormValues = z.infer<typeof jiraSchema>;
export type NotionFormValues = z.infer<typeof notionSchema>;
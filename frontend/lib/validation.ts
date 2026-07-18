import { z } from "zod";


export const jiraSchema = z.object({

  base_url: z
    .string()
    .trim()
    .url("Invalid Jira URL format"),


  admin_email: z
    .string()
    .trim()
    .email("Invalid email format"),


  api_key: z
    .string()
    .trim()
    .min(1, "API key is required"),

});



export const notionSchema = z.object({

  api_key: z
    .string()
    .trim()
    .min(1, "API key is required"),

});
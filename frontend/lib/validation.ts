import { z } from "zod";



export const jiraIntegrationSchema =
z.object({

base_url:
z
.string()
.trim()
.url("Invalid Jira URL"),


admin_email:
z
.string()
.trim()
.email("Invalid email"),


api_key:
z
.string()
.trim()
.min(1,"API key required"),


});




export const notionIntegrationSchema =
z.object({

api_key:
z
.string()
.trim()
.min(1,"API key required"),


});
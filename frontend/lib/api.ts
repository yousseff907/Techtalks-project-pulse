export async function getWorkspace() {
  return {
    id: "1",
    name: "Demo Workspace",
    jira_connected: false,
    notion_connected: false,
  };
}

// TODO: Replace with backend endpoint once available.
export async function updateJira(data: unknown) {
  console.log("Mock Jira update:", data);
  return { success: true };
}

// TODO: Replace with backend endpoint once available.
export async function updateNotion(data: unknown) {
  console.log("Mock Notion update:", data);
  return { success: true };
}
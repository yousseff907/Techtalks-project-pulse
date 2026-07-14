export interface ProviderAccount {
	id: string;
	name: string;
	email: string;
}

export interface WorkspaceMember {
	id: number;
	username: string;
	email: string;
	role: string;
	jira: ProviderAccount | null;
	notion: ProviderAccount | null;
}

export const mockMembers: WorkspaceMember[] = [
	{
		id: 1,
		username: "Alex Morgan",
		email: "alex@company.com",
		role: "Owner",
		jira: {
			id: "jira-1",
			name: "Alex Morgan",
			email: "alex@company.com",
		},
		notion: {
			id: "notion-1",
			name: "Alex Morgan",
			email: "alex@company.com",
		},
	},
	{
		id: 2,
		username: "Sarah Chen",
		email: "sarah@company.com",
		role: "Member",
		jira: {
			id: "jira-2",
			name: "Sarah Chen",
			email: "sarah@company.com",
		},
		notion: null,
	},
	{
		id: 3,
		username: "David Kim",
		email: "david@company.com",
		role: "Member",
		jira: null,
		notion: {
			id: "notion-3",
			name: "David Kim",
			email: "david@company.com",
		},
	},
	{
		id: 4,
		username: "Emily Wong",
		email: "emily@company.com",
		role: "Member",
		jira: null,
		notion: null,
	},
    {
        id: 5,
        username: "Michael Brown",
        email: "michael@company.com",
        role: "Member",
        jira: {
            id: "jira-5",
            name: "Michael Brown",
            email: "michael@company.com",
        },
        notion: null,
    },
    {
        id: 6,
        username: "Olivia Davis",
        email: "olivia@company.com",
        role: "Admin",
        jira: null,
        notion: {
            id: "notion-6",
            name: "Olivia Davis",
            email: "olivia@company.com",
        },
    }
];
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
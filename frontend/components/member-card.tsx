import { Card, CardContent } from "@/components/ui/card";
import { WorkspaceMember } from "@/app/workspaces/[workspace_id]/members/mock";

interface MemberCardProps {
	member: WorkspaceMember;
}

function ProviderSection({
	title,
	account,
}: {
	title: string;
	account: WorkspaceMember["jira"];
}) {
	return (
		<div className="rounded-lg border p-4">
			<p className="mb-2 text-sm font-medium">{title}</p>

			{account ? (
				<div className="space-y-1">
					<p className="font-medium">{account.name}</p>
					<p className="text-sm text-muted-foreground">
						{account.email}
					</p>
				</div>
			) : (
				<p className="text-sm text-muted-foreground">
					Not Connected
				</p>
			)}
		</div>
	);
}

export function MemberCard({
	member,
}: MemberCardProps) {
	return (
		<Card>
			<CardContent className="space-y-6 p-6">
				<div>
					<h2 className="text-lg font-semibold">
						{member.username}
					</h2>

					<p className="text-muted-foreground">
						{member.email}
					</p>

					<p className="mt-2 text-sm">
						Role:{" "}
						<span className="font-medium">
							{member.role}
						</span>
					</p>
				</div>

				<div className="grid gap-4 md:grid-cols-2">
					<ProviderSection
						title="Jira"
						account={member.jira}
					/>

					<ProviderSection
						title="Notion"
						account={member.notion}
					/>
				</div>
			</CardContent>
		</Card>
	);
}
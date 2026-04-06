import { getAgentSession, getAgentSessionContext } from "@/lib/server-api";
import { PageShell, appShellProps } from "../../../../../components/ui-helpers";
import { AgentSessionLiveView } from "./live-session";

export default async function RequestAgentSessionPage({
  params
}: {
  params: Promise<{ requestId: string; sessionId: string }>;
}) {
  const { requestId, sessionId } = await params;
  const [session, sessionContext] = await Promise.all([
    getAgentSession(requestId, sessionId),
    getAgentSessionContext(requestId, sessionId),
  ]);

  return (
    <PageShell
      {...appShellProps("/requests", `Agent Session: ${session.agent_label}`, "Native interactive agent collaboration attached directly to a governed request.")}
      contextPanel={<div />}
    >
      <AgentSessionLiveView requestId={requestId} initialSession={session} initialContext={sessionContext} />
    </PageShell>
  );
}

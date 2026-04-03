import React from "react";
import Link from "next/link";
import type { ReactNode } from "react";
import {
  Badge,
  Button,
  DataTable,
  EntityHeader,
  FilterPanel,
  KeyValueGrid,
  PageShell as SharedPageShell,
  PromotionGate,
  ReviewPanel,
  SectionHeading,
  Tabs as SharedTabs,
  TimeSeriesChart,
  Timeline,
  ConversationDock
} from "@rgp/ui";
import { primaryNavItems } from "./navigation";
import type { RequestStatus, RunStatus } from "@rgp/domain";
import { logoutAction } from "../app/login/actions";

export {
  Badge,
  Button,
  ConversationDock,
  DataTable,
  EntityHeader,
  FilterPanel,
  KeyValueGrid,
  PromotionGate,
  ReviewPanel,
  SectionHeading,
  TimeSeriesChart,
  Timeline
};

export function PageShell({
  title,
  subtitle,
  navItems,
  currentPath,
  contextPanel,
  children
}: {
  title: string;
  subtitle: string;
  navItems: readonly { label: string; href: string }[];
  currentPath: string;
  contextPanel?: ReactNode;
  children: ReactNode;
}) {
  return (
    <SharedPageShell
      title={title}
      subtitle={subtitle}
      navItems={navItems}
      currentPath={currentPath}
      contextPanel={contextPanel}
      headerActions={
        <form action={logoutAction}>
          <Button label="Log Out" tone="secondary" type="submit" />
        </form>
      }
      renderNavItem={(item, className) => (
        <Link key={item.href} href={item.href} prefetch className={className}>
          {item.label}
        </Link>
      )}
    >
      {children}
    </SharedPageShell>
  );
}

export function Tabs({
  tabs,
  activeKey
}: {
  tabs: { key: string; label: string; href?: string }[];
  activeKey: string;
}) {
  return (
    <SharedTabs
      tabs={tabs}
      activeKey={activeKey}
      renderTabLink={(item, className) => (
        <Link key={item.href} href={item.href} prefetch className={className}>
          {item.label}
        </Link>
      )}
    />
  );
}

export function appShellProps(currentPath: string, title: string, subtitle: string) {
  return {
    currentPath,
    title,
    subtitle,
    navItems: primaryNavItems
  };
}

export function MetricStack({ items }: { items: Array<{ label: string; value: ReactNode }> }) {
  return (
    <div className="space-y-4">
      {items.map((item) => (
        <div key={item.label} className="rounded-lg border border-chrome bg-slate-50 px-4 py-3">
          <div className="text-xs font-medium text-slate-500">{item.label}</div>
          <div className="mt-1 text-2xl font-semibold">{item.value}</div>
        </div>
      ))}
    </div>
  );
}

export function QueueTabs({
  activeKey,
  items
}: {
  activeKey: string;
  items: Array<{ key: string; label: string; href: string }>;
}) {
  return (
    <Tabs
      activeKey={activeKey}
      tabs={items.map((item) => ({
        key: item.key,
        label: item.label,
        href: item.href
      }))}
    />
  );
}

export function statusTone(status: RequestStatus | RunStatus | string): "neutral" | "info" | "warning" | "danger" | "success" {
  if (["approved", "completed", "promoted", "active", "connected", "published", "passed"].includes(status)) {
    return "success";
  }
  if (["failed", "rejected", "canceled", "blocked", "deprecated", "error"].includes(status)) {
    return "danger";
  }
  if (["awaiting_review", "under_review", "changes_requested", "waiting", "pending", "promotion_pending"].includes(status)) {
    return "warning";
  }
  if (["submitted", "validated", "planned", "in_execution", "running", "queued", "paused"].includes(status)) {
    return "info";
  }
  return "neutral";
}

export function formatDate(value: string) {
  return new Date(value).toLocaleString();
}

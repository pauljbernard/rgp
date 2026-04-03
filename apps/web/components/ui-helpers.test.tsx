import { render, screen } from "@testing-library/react";
import React from "react";
import { MetricStack, QueueTabs } from "./ui-helpers";

describe("web ui helpers", () => {
  it("renders metric stack labels and values", () => {
    render(<MetricStack items={[{ label: "Open Requests", value: 12 }, { label: "Blocked", value: 3 }]} />);

    expect(screen.getByText("Open Requests")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("Blocked")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders queue tabs as navigation links", () => {
    render(
      <QueueTabs
        activeKey="all"
        items={[
          { key: "all", label: "All Requests", href: "/requests" },
          { key: "blocked", label: "Blocked Requests", href: "/requests/blocked" }
        ]}
      />
    );

    expect(screen.getByRole("link", { name: "All Requests" })).toHaveAttribute("href", "/requests");
    expect(screen.getByRole("link", { name: "Blocked Requests" })).toHaveAttribute("href", "/requests/blocked");
  });
});

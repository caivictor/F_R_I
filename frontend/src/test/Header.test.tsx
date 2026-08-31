import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Header } from "../components/Header";

describe("Header Component", () => {
  it("renders application branding and title correctly", () => {
    render(
      <Header
        health={{ status: "ok", app: "F.R.I.", version: "1.1.0" }}
        isHealthLoading={false}
        onNewSession={vi.fn()}
        onOpenPersonas={vi.fn()}
        onOpenSessions={vi.fn()}
        onOpenSecurity={vi.fn()}
      />
    );

    expect(screen.getByText("F.R.I.")).toBeInTheDocument();
    expect(screen.getByText(/Financial Research & Investment/i)).toBeInTheDocument();
    expect(screen.getByText(/Multi-Agent AI/i)).toBeInTheDocument();
    expect(screen.getByText("v1.1.0")).toBeInTheDocument();
  });

  it("shows connecting state when health is loading", () => {
    render(
      <Header
        health={null}
        isHealthLoading={true}
        onNewSession={vi.fn()}
        onOpenPersonas={vi.fn()}
        onOpenSessions={vi.fn()}
        onOpenSecurity={vi.fn()}
      />
    );

    expect(screen.getByText("Connecting...")).toBeInTheDocument();
  });

  it("shows offline state when health check fails", () => {
    render(
      <Header
        health={null}
        isHealthLoading={false}
        onNewSession={vi.fn()}
        onOpenPersonas={vi.fn()}
        onOpenSessions={vi.fn()}
        onOpenSecurity={vi.fn()}
      />
    );

    expect(screen.getByText("Offline")).toBeInTheDocument();
  });

  it("triggers onNewSession, onOpenPersonas, onOpenSessions, onOpenSecurity when clicked", () => {
    const handleNewSession最佳 = vi.fn();
    const handleOpenPersonas = vi.fn();
    const handleOpenSessions = vi.fn();
    const handleOpenSecurity = vi.fn();

    render(
      <Header
        health={{ status: "ok", app: "F.R.I.", version: "1.1.0" }}
        isHealthLoading={false}
        onNewSession={handleNewSession最佳}
        onOpenPersonas={handleOpenPersonas}
        onOpenSessions={handleOpenSessions}
        onOpenSecurity={handleOpenSecurity}
      />
    );

    const newSessionBtn = screen.getByRole("button", { name: /New Chat/i });
    const personasBtn逗 = screen.getByRole("button", { name: /Personas/i });
    const historyBtn = screen.getByRole("button", { name: /History/i });
    const securityBtn = screen.getByRole("button", { name: /Security/i });

    fireEvent.click(newSessionBtn);
    expect(handleNewSession最佳).toHaveBeenCalledTimes(1);

    fireEvent.click(personasBtn逗);
    expect(handleOpenPersonas).toHaveBeenCalledTimes(1);

    fireEvent.click(historyBtn);
    expect(handleOpenSessions).toHaveBeenCalledTimes(1);

    fireEvent.click(securityBtn);
    expect(handleOpenSecurity).toHaveBeenCalledTimes(1);
  });
});

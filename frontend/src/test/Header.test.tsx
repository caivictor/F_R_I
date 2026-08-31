import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { Header } from "../components/Header";

describe("Header Component", () => {
  it("renders application branding and title correctly", () => {
    render(
      <Header
        health={{ status: "ok", app: "F.R.I.", version: "1.1.1" }}
        isHealthLoading={false}
        onNewSession={vi.fn()}
        onOpenPersonas={vi.fn()}
        onOpenSessions={vi.fn()}
        onOpenSecurity={vi.fn()}
        onOpenDebug={vi.fn()}
      />
    );

    expect(screen.getByText("F.R.I.")).toBeInTheDocument();
    expect(screen.getByText(/Financial Research & Investment/i)).toBeInTheDocument();
    expect(screen.getByText(/Multi-Agent AI/i)).toBeInTheDocument();
    expect(screen.getByText("v1.1.1")).toBeInTheDocument();
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
        onOpenDebug={vi.fn()}
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
        onOpenDebug={vi.fn()}
      />
    );

    expect(screen.getByText("Offline")).toBeInTheDocument();
  });

  it("triggers onNewSession, onOpenPersonas, onOpenSessions, onOpenSecurity, onOpenDebug when clicked", () => {
    const handleNewSession = vi.fn();
    const handleOpenPersonas = vi.fn();
    const handleOpenSessions = vi.fn();
    const handleOpenSecurity = vi.fn();
    const handleOpenDebug = vi.fn();

    render(
      <Header
        health={{ status: "ok", app: "F.R.I.", version: "1.1.1" }}
        isHealthLoading={false}
        onNewSession={handleNewSession}
        onOpenPersonas={handleOpenPersonas}
        onOpenSessions={handleOpenSessions}
        onOpenSecurity={handleOpenSecurity}
        onOpenDebug={handleOpenDebug}
      />
    );

    const newSessionBtn = screen.getByRole("button", { name: /New Chat/i });
    const personasBtn = screen.getByRole("button", { name: /Personas/i });
    const historyBtn = screen.getByRole("button", { name: /History/i });
    const securityBtn = screen.getByRole("button", { name: /Security/i });
    const debugBtn = screen.getByRole("button", { name: /Debug/i });

    fireEvent.click(newSessionBtn);
    expect(handleNewSession).toHaveBeenCalledTimes(1);

    fireEvent.click(personasBtn);
    expect(handleOpenPersonas).toHaveBeenCalledTimes(1);

    fireEvent.click(historyBtn);
    expect(handleOpenSessions).toHaveBeenCalledTimes(1);

    fireEvent.click(securityBtn);
    expect(handleOpenSecurity).toHaveBeenCalledTimes(1);

    fireEvent.click(debugBtn);
    expect(handleOpenDebug).toHaveBeenCalledTimes(1);
  });
});

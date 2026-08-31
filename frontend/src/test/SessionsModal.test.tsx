import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { SessionsModal } from "../components/SessionsModal";
import type { ChatSessionSummary } from "../types";

describe("SessionsModal Component", () => {
  const mockSessions: ChatSessionSummary[] = [
    {
      session_id: "sess_1",
      title: "Tech Stock Exploration",
      created_at: "2026-08-30 10:00:00 UTC",
      updated_at: "2026-08-30 10:05:00 UTC",
      message_count: 4,
      last_ticker: "NVDA",
      summary: "Evaluated NVDA and AAPL",
    },
    {
      session_id: "sess_2",
      title: "Portfolio Check",
      created_at: "2026-08-30 09:00:00 UTC",
      updated_at: "2026-08-30 09:02:00 UTC",
      message_count: 2,
      last_ticker: "MSFT",
    },
  ];

  it("does not render when isOpen is false", () => {
    const { container } = render(
      <SessionsModal
        isOpen={false}
        sessions={mockSessions}
        currentSessionId="sess_1"
        isLoading={false}
        onClose={vi.fn()}
        onSelectSession={vi.fn()}
        onDeleteSession={vi.fn()}
        onNewSession={vi.fn()}
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it("renders sessions list and active badge when open", () => {
    render(
      <SessionsModal
        isOpen={true}
        sessions={mockSessions}
        currentSessionId="sess_1"
        isLoading={false}
        onClose={vi.fn()}
        onSelectSession={vi.fn()}
        onDeleteSession={vi.fn()}
        onNewSession={vi.fn()}
      />
    );

    expect(screen.getByText(/Chat History & Context Memory/i)).toBeInTheDocument();
    expect(screen.getByText("Tech Stock Exploration")).toBeInTheDocument();
    expect(screen.getByText("Portfolio Check")).toBeInTheDocument();
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(screen.getByText("$NVDA")).toBeInTheDocument();
  });

  it("triggers onSelectSession when clicking a session item", () => {
    const handleSelect = vi.fn();
    const handleClose = vi.fn();

    render(
      <SessionsModal
        isOpen={true}
        sessions={mockSessions}
        currentSessionId="sess_1"
        isLoading={false}
        onClose={handleClose}
        onSelectSession={handleSelect}
        onDeleteSession={vi.fn()}
        onNewSession={vi.fn()}
      />
    );

    fireEvent.click(screen.getByText("Portfolio Check"));
    expect(handleSelect).toHaveBeenCalledWith("sess_2");
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});

"""Comprehensive Multi-Turn QA Test Suite for Master Agent Conversational Memory, Intent Understanding, Context Compression, and Debug Log Integrity across 10, 20, 50, and 100 Turns."""

import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.db.database import db
from backend.app.agents.manager import ManagerAgent, SessionState


def _generate_turn_dialogue_plan(target_turns: int):
    """Generate a structured, realistic multi-turn conversation plan covering all agent workflows and conversational memory."""
    patterns = [
        # Pattern 0: Initial Discovery
        {"prompt": "Discover top market news and trending companies", "expected_in_response": ["Executive Investment Discovery Briefing", "Market Research"]},
        # Pattern 1: Ticker Focus
        {"prompt": "Analyze Apple fundamentals and capital efficiency", "expected_in_response": ["Apple Inc", "AAPL", "Long-Term Investment Dossier"]},
        # Pattern 2: Pronoun Resolution
        {"prompt": "What is its return on invested capital and gross margin?", "expected_in_response": ["AAPL", "%"]},
        # Pattern 3: Pronoun Valuation Multiple
        {"prompt": "What about its valuation and P/E ratio?", "expected_in_response": ["AAPL", "P/E"]},
        # Pattern 4: Portfolio NAV
        {"prompt": "Show my portfolio balance and positions", "expected_in_response": ["Portfolio", "Cash Balance"]},
        # Pattern 5: Cash Deposit
        {"prompt": "Deposit $10,000 into my investment account", "expected_in_response": ["Cash Deposit Successful", "$10,000.00"]},
        # Pattern 6: New Entity Focus
        {"prompt": "Analyze Microsoft", "expected_in_response": ["Microsoft Corporation", "MSFT"]},
        # Pattern 7: Trade Intent with Pronoun
        {"prompt": "Buy 10 shares of it", "expected_in_response": ["Trade Order Confirmation Required", "MSFT", "Confirm purchase?"]},
        # Pattern 8: Trade Cancellation
        {"prompt": "No, cancel this order", "expected_in_response": ["cancelled", "MSFT"]},
        # Pattern 9: Multi-Item Reference
        {"prompt": "Why didn't you research all five recommendations?", "expected_in_response": ["Multi-Asset Comparative Analysis", "Comparative Financial Scorecard"]},
        # Pattern 10: Conversational Guidance
        {"prompt": "What should we explore next today?", "expected_in_response": ["Manager Agent"]},
        # Pattern 11: Quantitative Comparison
        {"prompt": "Analyze NVDA fundamentals and moat", "expected_in_response": ["NVIDIA Corporation", "NVDA"]},
        # Pattern 12: Cash Withdrawal
        {"prompt": "Withdraw $2,000 from cash", "expected_in_response": ["Cash Withdrawal Successful", "$2,000.00"]},
        # Pattern 13: Watchlist Exploration
        {"prompt": "Analyze all candidate companies and recommendations", "expected_in_response": ["Multi-Asset", "Scorecard"]},
        # Pattern 14: Direct Trade Execution
        {"prompt": "Buy 5 shares of NVDA", "expected_in_response": ["Trade Order Confirmation Required", "NVDA"]},
        # Pattern 15: Affirmative Execution
        {"prompt": "Yes, proceed with order", "expected_in_response": ["Trade Confirmation & Execution", "NVDA", "Remaining Cash Balance"]},
        # Pattern 16: Holdings Audit
        {"prompt": "Display my transaction audit history", "expected_in_response": ["Transaction", "Audit History", "BUY"]},
        # Pattern 17: Dividend Logging
        {"prompt": "Log a dividend of $1.50 per share for NVDA", "expected_in_response": ["Dividend Distribution Recorded", "NVDA"]},
        # Pattern 18: Re-check Holdings
        {"prompt": "What are my current holdings and cost basis?", "expected_in_response": ["NVDA", "Holdings"]},
        # Pattern 19: Strategy Feedback
        {"prompt": "How is our portfolio performing so far?", "expected_in_response": ["Portfolio", "Net Asset Value"]},
    ]

    dialogue = []
    for turn_idx in range(target_turns):
        template = patterns[turn_idx % len(patterns)]
        dialogue.append({
            "turn": turn_idx + 1,
            "prompt": template["prompt"],
            "expected_keywords": template["expected_in_response"],
        })
    return dialogue


@pytest.mark.parametrize("turn_count", [10, 20, 50, 100])
@pytest.mark.asyncio
async def test_multiturn_conversations_and_exact_debug_log_matching(turn_count: int):
    """QA Multi-Turn Suite: Test 10, 20, 50, and 100 turns in a single persistent session.
    
    Verifies:
    1. Master Agent understands multi-turn commands and pronouns.
    2. Entity memory and rolling context compression remain intact without degradation.
    3. Exact 1:1 matching between session conversation turns and captured SQLite debug logs (prompt, response, context data).
    """
    session_id = f"qa_multiturn_session_{turn_count}_turns"
    # Ensure fresh session
    db.delete_session(session_id)

    dialogue_plan = _generate_turn_dialogue_plan(turn_count)
    conversation_transcript = []

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Execute each turn sequentially in the exact same session
        for step in dialogue_plan:
            turn_num = step["turn"]
            user_prompt = step["prompt"]

            res = await client.post(
                "/api/chat",
                json={"message": user_prompt, "session_id": session_id},
            )
            assert res.status_code == 200, f"Turn {turn_num} failed with status {res.status_code}"
            data = res.json()
            assert data["session_id"] == session_id

            response_text = data["response"]
            assert response_text is not None and len(response_text) > 0, f"Turn {turn_num} returned empty response"

            # Check expected keywords for this turn
            for kw in step["expected_keywords"]:
                assert kw.lower() in response_text.lower(), f"Turn {turn_num} ('{user_prompt}') missing expected keyword '{kw}'. Response: {response_text[:300]}..."

            conversation_transcript.append({
                "turn": turn_num,
                "user_prompt": user_prompt,
                "assistant_response": response_text,
            })

        # --- QA Integrity Verification: SQLite Session & Debug Logs Matching ---
        
        # 1. Fetch Session Details from /api/chat/sessions/{session_id}
        sess_details_res = await client.get(f"/api/chat/sessions/{session_id}")
        assert sess_details_res.status_code == 200
        sess_data = sess_details_res.json()
        assert sess_data["session_id"] == session_id

        # Total messages in chat_messages should equal 2 * turn_count (1 user + 1 assistant per turn)
        messages = sess_data["messages"]
        assert len(messages) == turn_count * 2, f"Expected {turn_count * 2} messages in DB, found {len(messages)}"

        # 2. Fetch Debug Logs from /api/chat/sessions/{session_id}/debug
        debug_res = await client.get(f"/api/chat/sessions/{session_id}/debug?limit=500")
        assert debug_res.status_code == 200
        debug_payload = debug_res.json()
        assert debug_payload["session_id"] == session_id
        
        debug_logs = debug_payload["debug_logs"]
        assert len(debug_logs) >= turn_count, f"Expected at least {turn_count} debug logs, found {len(debug_logs)}"

        # 3. Exact 1:1 Matching: Verify every turn's input, output, and context payload
        turn_logs = [log for log in debug_logs if log.get("agent") == "manager" and log.get("status") == "turn_completed"]
        assert len(turn_logs) == turn_count, f"Expected {turn_count} turn_completed debug logs, found {len(turn_logs)}"

        for idx, transcript_item in enumerate(conversation_transcript):
            turn_no = transcript_item["turn"]
            expected_input = transcript_item["user_prompt"]
            expected_output = transcript_item["assistant_response"]

            # Match in messages array
            user_msg = messages[idx * 2]
            asst_msg = messages[idx * 2 + 1]

            assert user_msg["role"] == "user"
            assert user_msg["content"] == expected_input, f"Turn {turn_no} user message mismatch in chat_messages"

            assert asst_msg["role"] == "assistant"
            assert asst_msg["content"] == expected_output, f"Turn {turn_no} assistant message mismatch in chat_messages"

            # Match in turn_logs array chronologically
            matched_log = turn_logs[idx]
            assert matched_log["prompt"] == expected_input, f"Turn {turn_no} prompt mismatch at turn_logs[{idx}]"
            assert matched_log["session_id"] == session_id
            assert matched_log["agent"] == "manager"
            assert matched_log["response"] == expected_output, f"Turn {turn_no} response mismatch in llm_debug_logs"
            assert matched_log["context_data"] is not None
            assert matched_log["context_data"]["user_query"] == expected_input
            assert matched_log["latency_ms"] >= 0.0

        # 4. Memory & Context Compression Check on Higher Turn Counts (50 and 100 turns)
        if turn_count >= 20:
            memory_data = sess_data.get("memory")
            assert memory_data is not None
            assert memory_data.get("summary") is not None
            assert "Session Context Summary" in memory_data["summary"]

    # Clean up test session
    db.delete_session(session_id)

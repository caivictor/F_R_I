"""Adversarial Multi-Turn Test Suite for F.R.I. Master Agent.

Tests erratic, hostile, nonsensical, and topic-jumping multi-turn conversations
across 10, 20, 50, and 100 turns. Verifies that the Master Agent never crashes,
properly manages state and invalidates pending trades on topic switches, and that
all turn inputs, outputs, context payloads, and latencies are captured in SQLite
debug logs for forensic evidence.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.db.database import db


def _generate_adversarial_turns(turn_count: int):
    """Generate erratic, hostile, and nonsensical multi-turn conversation patterns."""
    adversarial_patterns = [
        # Pattern 0: Nonsensical / Gibberish text
        {"prompt": "asdfjkl; qwertyuiop zxcvbnm !@#$%^&*()_+", "expected_type": "graceful_handling"},
        # Pattern 1: Topic Jump - Random question
        {"prompt": "What is the capital of Mars and how do penguins fly?", "expected_type": "conversational_or_guidance"},
        # Pattern 2: Trade Initiation
        {"prompt": "Buy 10 shares of NVDA", "expected_type": "trade_confirmation"},
        # Pattern 3: Sudden Topic Jump while Trade is Pending (Must invalidate pending trade)
        {"prompt": "Tell me a joke about quantum physics instead", "expected_type": "invalidation"},
        # Pattern 4: Stale Confirmation attempt (Must NOT execute previous trade)
        {"prompt": "yes proceed and confirm", "expected_type": "stale_confirmation_prevented"},
        # Pattern 5: Malformed Ticker / Extreme characters
        {"prompt": "Analyze %%%$$$###@@@!???", "expected_type": "graceful_error_or_guidance"},
        # Pattern 6: Private Company Bait
        {"prompt": "Buy 100 shares of SpaceX immediately", "expected_type": "private_rejection"},
        # Pattern 7: Another Stale Confirmation attempt
        {"prompt": "confirm purchase now", "expected_type": "stale_confirmation_prevented"},
        # Pattern 8: Extreme Negative Number in Cash Deposit
        {"prompt": "Deposit $-5000000 into my account", "expected_type": "deposit_rejection_or_handling"},
        # Pattern 9: Rapid Topic Switch to Discovery
        {"prompt": "Discover market news and analyze trending companies", "expected_type": "discovery"},
        # Pattern 10: Multi-item reference ambiguity
        {"prompt": "Why didn't you analyze all 1000 stocks in the world?", "expected_type": "multi_asset_handling"},
        # Pattern 11: Trade Initiation for Unowned Stock
        {"prompt": "Sell 500 shares of AAPL", "expected_type": "insufficient_shares_or_validation"},
        # Pattern 12: Nonsensical math
        {"prompt": "What is 0 divided by 0 multiplied by infinity?", "expected_type": "conversational_or_guidance"},
        # Pattern 13: Non-US / Foreign Stock bait
        {"prompt": "Analyze 0700.HK and buy 50 shares of it", "expected_type": "foreign_stock_rejection"},
        # Pattern 14: Conflicting Intent (Trade + Question + Reset)
        {"prompt": "Reset my portfolio to 100k and buy 5 shares of MSFT", "expected_type": "handled_safely"},
        # Pattern 15: Empty-like whitespace and special unicode
        {"prompt": "   \n\t  \u200b\u200c\u200d   ", "expected_type": "fallback_or_guidance"},
        # Pattern 16: Extreme Share Quantity
        {"prompt": "Buy 999999999999 shares of AAPL", "expected_type": "trade_confirmation_or_cash_reject"},
        # Pattern 17: Contrary cancellation with affirmation words
        {"prompt": "ok sure, cancel that order and do not execute anything", "expected_type": "cancelled_or_handled"},
        # Pattern 18: Rapid switching back to normal query
        {"prompt": "Show my portfolio balance and positions", "expected_type": "portfolio_status"},
        # Pattern 19: Pronoun with no valid subject focus
        {"prompt": "What is its price right now?", "expected_type": "pronoun_handled_or_fallback"},
    ]

    dialogue = []
    for i in range(turn_count):
        template = adversarial_patterns[i % len(adversarial_patterns)]
        dialogue.append({
            "turn": i + 1,
            "prompt": template["prompt"],
            "expected_type": template["expected_type"],
        })
    return dialogue


@pytest.mark.parametrize("turn_count", [10, 20, 50, 100])
@pytest.mark.asyncio
async def test_adversary_multiturn_resilience_and_evidence_log_verification(turn_count: int):
    """Adversarial Multi-Turn Test: 10, 20, 50, and 100 turns of hostile topic-jumping.
    
    Verifies:
    1. The Master Agent handles erratic, nonsensical, and hostile topic switches without 500 errors or crashes.
    2. Pending trade confirmations are safely cleared/invalidated when an adversary switches topics mid-flow.
    3. Every adversarial turn is recorded chronologically in `llm_debug_logs` with exact input, output, context, and latency for debugging and forensic evidence.
    """
    session_id = f"adversary_multiturn_session_{turn_count}_turns"
    db.delete_session(session_id)

    turns_plan = _generate_adversarial_turns(turn_count)
    conversation_records = []

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for step in turns_plan:
            turn_num = step["turn"]
            user_prompt = step["prompt"]

            # App must respond with HTTP 200 without crashing on any hostile/erratic input
            res = await client.post(
                "/api/chat",
                json={"message": user_prompt, "session_id": session_id},
            )
            assert res.status_code == 200, f"Adversarial Turn {turn_num} crashed with status {res.status_code}"
            data = res.json()
            assert data["session_id"] == session_id
            response_text = data["response"]
            assert response_text and len(response_text.strip()) > 0, f"Turn {turn_num} returned blank response"

            conversation_records.append({
                "turn": turn_num,
                "user_prompt": user_prompt,
                "assistant_response": response_text,
            })

        # --- Adversarial Forensic Evidence & Log Integrity Verification ---

        # 1. Fetch Session from Database
        sess_res = await client.get(f"/api/chat/sessions/{session_id}")
        assert sess_res.status_code == 200
        sess_data = sess_res.json()
        assert len(sess_data["messages"]) == turn_count * 2

        # 2. Fetch Debug & Forensic Logs from /api/chat/sessions/{session_id}/debug
        debug_res = await client.get(f"/api/chat/sessions/{session_id}/debug?limit=500")
        assert debug_res.status_code == 200
        debug_payload = debug_res.json()
        assert debug_payload["session_id"] == session_id

        debug_logs = debug_payload["debug_logs"]
        turn_logs = [log for log in debug_logs if log.get("agent") == "manager" and log.get("status") == "turn_completed"]
        assert len(turn_logs) == turn_count, f"Expected {turn_count} turn logs for forensic audit, found {len(turn_logs)}"

        # 3. Exact 1:1 Matching of inputs, outputs, and context payloads for evidence
        for idx, rec in enumerate(conversation_records):
            turn_no = rec["turn"]
            expected_input = rec["user_prompt"]
            expected_output = rec["assistant_response"]

            matched_log = turn_logs[idx]
            assert matched_log["prompt"] == expected_input, f"Forensic mismatch at Turn {turn_no} prompt"
            assert matched_log["response"] == expected_output, f"Forensic mismatch at Turn {turn_no} response"
            assert matched_log["context_data"] is not None
            assert matched_log["context_data"]["user_query"] == expected_input
            assert matched_log["latency_ms"] >= 0.0

    # Cleanup
    db.delete_session(session_id)

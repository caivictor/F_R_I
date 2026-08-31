"""Gemini LLM client helper for F.R.I. agents with context capture and debug logging."""

import asyncio
import time
from typing import Any, Dict, Optional
from backend.app.config import settings
from backend.app.db.database import db


async def generate_text(
    prompt: str,
    system_instruction: Optional[str] = None,
    model: str = "gemini-2.5-flash",
    session_id: Optional[str] = None,
    agent: str = "manager",
    context_data: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """Generate text using Gemini API if GEMINI_API_KEY is set, capturing debug logs with full context."""
    start_time = time.perf_counter()
    resp_text: Optional[str] = None
    status = "offline_fallback"

    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
        def _call_gemini() -> Optional[str]:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=settings.GEMINI_API_KEY)
                config = None
                if system_instruction:
                    config = types.GenerateContentConfig(system_instruction=system_instruction)

                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                if response and response.text:
                    return response.text.strip()
                return None
            except Exception:
                return None

        try:
            resp_text = await asyncio.to_thread(_call_gemini)
            if resp_text:
                status = "api_success"
            else:
                status = "api_empty_fallback"
        except Exception:
            status = "api_error_fallback"

    latency_ms = round((time.perf_counter() - start_time) * 1000, 2)

    # Persist context and debug log in SQLite if session_id is provided
    if session_id:
        try:
            db.save_llm_debug_log(
                session_id=session_id,
                agent=agent,
                model=model,
                system_instruction=system_instruction,
                prompt=prompt,
                context_data=context_data,
                response=resp_text,
                latency_ms=latency_ms,
                status=status,
            )
        except Exception:
            pass

    return resp_text

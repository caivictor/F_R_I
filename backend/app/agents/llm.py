"""Gemini LLM client helper for F.R.I. agents with graceful fallback."""

import asyncio
from typing import Optional
from backend.app.config import settings


async def generate_text(prompt: str, system_instruction: Optional[str] = None, model: str = "gemini-2.5-flash") -> Optional[str]:
    """Generate text using Gemini Flash API if GEMINI_API_KEY is configured.
    
    Returns None if GEMINI_API_KEY is not set or if an error occurs,
    allowing agents to fall back seamlessly to local deterministic synthesis.
    """
    if not settings.GEMINI_API_KEY or not settings.GEMINI_API_KEY.strip():
        return None

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
        return await asyncio.to_thread(_call_gemini)
    except Exception:
        return None

"""Briefing service — turns fired signals + evidence into readable AI briefs.

Uses Groq free tier via LiteLLM. Falls back to pre-generated briefs from seed
data when the LLM is unavailable.
"""

from __future__ import annotations

import json
import os
from typing import Any

from src.config import settings
from src.logging_config import get_logger
from src.seed.data import get_brief_for_signal

from .prompts import DEFAULT_VERSION, PROMPT_VERSIONS

log = get_logger(__name__)


def _format_evidence(evidence: list[dict]) -> str:
    """Format evidence list into text for the prompt."""
    if not evidence:
        return "No additional evidence available."

    lines = []
    for i, e in enumerate(evidence, 1):
        line = f"{i}. [{e.get('type', 'unknown')}] {e.get('title', 'Untitled')}"
        if e.get("detail"):
            line += f"\n   {e['detail']}"
        if e.get("source"):
            line += f"\n   Source: {e['source']}"
        if e.get("url"):
            line += f"\n   URL: {e['url']}"
        if e.get("timestamp"):
            line += f"\n   Timestamp: {e['timestamp']}"
        lines.append(line)

    return "\n\n".join(lines)


async def generate_brief(
    signal: dict,
    prompt_version: str = DEFAULT_VERSION,
) -> dict:
    """Generate an AI brief for a fired signal.

    Returns a dict with sections: what_happened, why_it_matters,
    supporting_evidence, risks.

    Falls back to seed data briefs if LLM call fails.
    """
    prompt_config = PROMPT_VERSIONS.get(prompt_version, PROMPT_VERSIONS[DEFAULT_VERSION])

    evidence = signal.get("evidence", [])
    evidence_text = _format_evidence(evidence)

    user_prompt = prompt_config["user"].format(
        signal_type=signal.get("type", "unknown"),
        ticker=signal.get("ticker", ""),
        company_name=signal.get("company_name", ""),
        strength=signal.get("strength", ""),
        sentiment=signal.get("sentiment", ""),
        score=signal.get("score", 0),
        headline=signal.get("headline", ""),
        detail=signal.get("detail", ""),
        evidence_text=evidence_text,
    )

    try:
        result = await _call_llm(
            system=prompt_config["system"],
            user=user_prompt,
        )

        # Parse JSON response from LLM
        brief_data = _parse_brief_response(result)

        return {
            "signal_id": signal.get("id", ""),
            "ticker": signal.get("ticker", ""),
            "generated_at": signal.get("detected_at", ""),
            "prompt_version": prompt_version,
            "sections": brief_data,
            "evidence": evidence,
        }

    except Exception as e:
        log.warning("brief_generation_failed", signal_id=signal.get("id"), error=str(e))
        # Fall back to seed brief
        seed_brief = get_brief_for_signal(signal.get("id", ""))
        if seed_brief:
            return {**seed_brief, "evidence": evidence}

        # Last resort: construct from signal data directly
        return {
            "signal_id": signal.get("id", ""),
            "ticker": signal.get("ticker", ""),
            "generated_at": signal.get("detected_at", ""),
            "prompt_version": prompt_version,
            "sections": {
                "what_happened": signal.get("headline", "Signal detected."),
                "why_it_matters": signal.get("detail", ""),
                "supporting_evidence": evidence,
                "risks": "Unable to generate AI analysis. Review the raw signal data and evidence sources directly.",
            },
            "evidence": evidence,
        }


def _parse_brief_response(raw: str) -> dict:
    """Parse the LLM JSON response into brief sections."""
    # Try to extract JSON from the response
    raw = raw.strip()

    # Handle markdown code blocks
    if raw.startswith("```"):
        lines = raw.split("\n")
        # Remove first and last lines (```json and ```)
        json_lines = []
        inside = False
        for line in lines:
            if line.strip().startswith("```") and not inside:
                inside = True
                continue
            if line.strip() == "```" and inside:
                break
            if inside:
                json_lines.append(line)
        raw = "\n".join(json_lines)

    try:
        data = json.loads(raw)
        return {
            "what_happened": data.get("what_happened", ""),
            "why_it_matters": data.get("why_it_matters", ""),
            "supporting_evidence": data.get("supporting_evidence", ""),
            "risks": data.get("risks", ""),
        }
    except json.JSONDecodeError:
        # If JSON parsing fails, try to extract sections from plain text
        return {
            "what_happened": raw[:500] if raw else "",
            "why_it_matters": "",
            "supporting_evidence": "",
            "risks": "",
        }


async def _call_llm(system: str, user: str) -> str:
    """Call Groq LLM via LiteLLM."""
    import litellm

    if settings.groq_api_key:
        os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key)

    model = settings.llm_model
    response = await litellm.acompletion(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.2,
        max_tokens=800,
    )
    return response.choices[0].message.content or ""

"""Versioned prompt templates for brief generation.

Each prompt version is a dict with a system message and user message template.
This allows A/B testing and iterating on prompt quality without code changes.
"""

from __future__ import annotations

BRIEF_V1 = {
    "version": "v1",
    "system": (
        "You are AlphaRadar's intelligence briefing engine. You produce concise, "
        "source-backed investment intelligence briefs from detected signals.\n\n"
        "Rules:\n"
        "- NEVER give direct buy/sell/hold recommendations\n"
        "- ALWAYS reference source data and timestamps\n"
        "- Acknowledge uncertainty and alternative explanations\n"
        "- Use plain language — write for a smart retail investor, not a quant\n"
        "- Be concise: each section should be 2-4 sentences max"
    ),
    "user": (
        "Generate an intelligence brief for the following signal.\n\n"
        "## Signal\n"
        "- Type: {signal_type}\n"
        "- Ticker: {ticker} ({company_name})\n"
        "- Strength: {strength} | Sentiment: {sentiment} | Score: {score}/100\n"
        "- Headline: {headline}\n"
        "- Detail: {detail}\n\n"
        "## Evidence\n"
        "{evidence_text}\n\n"
        "## Output Format (respond in exactly this JSON structure)\n"
        '{{\n'
        '  "what_happened": "One paragraph: what the signal detected and the raw facts",\n'
        '  "why_it_matters": "One paragraph: why this matters for investors, with historical context if available",\n'
        '  "supporting_evidence": "Bullet points referencing each evidence source with timestamps",\n'
        '  "risks": "One paragraph: what could invalidate this signal or alternative explanations"\n'
        '}}'
    ),
}

BRIEF_V2 = {
    "version": "v2",
    "system": (
        "You are AlphaRadar, an alternative data analyst that writes brief intelligence "
        "reports for retail investors. Your briefs are factual, source-cited, and actionable "
        "without ever recommending specific trades.\n\n"
        "Tone: Bloomberg Terminal meets plain English. No jargon without explanation."
    ),
    "user": (
        "Write a brief for this signal:\n\n"
        "Signal: [{signal_type}] {headline}\n"
        "Company: {ticker} — {company_name}\n"
        "Strength: {strength} | Sentiment: {sentiment} | Score: {score}\n"
        "Detail: {detail}\n\n"
        "Evidence:\n{evidence_text}\n\n"
        "Respond with JSON:\n"
        '{{\n'
        '  "what_happened": "...",\n'
        '  "why_it_matters": "...",\n'
        '  "supporting_evidence": "...",\n'
        '  "risks": "..."\n'
        '}}'
    ),
}

# Registry of all prompt versions
PROMPT_VERSIONS = {
    "v1": BRIEF_V1,
    "v2": BRIEF_V2,
}

DEFAULT_VERSION = "v1"

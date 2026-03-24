"""Tests for briefing service."""

import sys
sys.path.insert(0, "src")

from src.briefing.prompts import PROMPT_VERSIONS, DEFAULT_VERSION, BRIEF_V1, BRIEF_V2
from src.briefing.service import _format_evidence, _parse_brief_response


def test_prompt_versions_exist():
    assert "v1" in PROMPT_VERSIONS
    assert "v2" in PROMPT_VERSIONS
    assert DEFAULT_VERSION in PROMPT_VERSIONS


def test_prompt_v1_has_required_fields():
    assert "version" in BRIEF_V1
    assert "system" in BRIEF_V1
    assert "user" in BRIEF_V1


def test_prompt_v2_has_required_fields():
    assert "version" in BRIEF_V2
    assert "system" in BRIEF_V2
    assert "user" in BRIEF_V2


def test_prompts_contain_no_buy_sell():
    for version, prompt in PROMPT_VERSIONS.items():
        system = prompt["system"].lower()
        has_prohibition = ("never" in system or "not" in system or "without" in system)
        has_target = ("buy" in system or "sell" in system or "recommend" in system or "trade" in system)
        assert has_prohibition and has_target, \
            f"Prompt {version} should explicitly prohibit buy/sell recommendations"


def test_format_evidence_empty():
    result = _format_evidence([])
    assert "No additional evidence" in result


def test_format_evidence_with_items():
    evidence = [
        {"type": "sec_filing", "title": "Test Filing", "detail": "Some detail", "source": "SEC", "url": "https://sec.gov", "timestamp": "2026-03-20T00:00:00"},
    ]
    result = _format_evidence(evidence)
    assert "Test Filing" in result
    assert "SEC" in result
    assert "https://sec.gov" in result


def test_parse_brief_response_valid_json():
    raw = '{"what_happened": "test", "why_it_matters": "test2", "supporting_evidence": "test3", "risks": "test4"}'
    result = _parse_brief_response(raw)
    assert result["what_happened"] == "test"
    assert result["why_it_matters"] == "test2"
    assert result["risks"] == "test4"


def test_parse_brief_response_markdown_json():
    raw = '```json\n{"what_happened": "test", "why_it_matters": "t2", "supporting_evidence": "t3", "risks": "t4"}\n```'
    result = _parse_brief_response(raw)
    assert result["what_happened"] == "test"


def test_parse_brief_response_invalid_json():
    raw = "This is not JSON at all"
    result = _parse_brief_response(raw)
    # Should not crash, returns raw text as what_happened
    assert result["what_happened"] != ""


def test_user_prompt_template_formatting():
    prompt = BRIEF_V1["user"]
    # Ensure all template vars can be filled
    result = prompt.format(
        signal_type="hiring_surge",
        ticker="NVDA",
        company_name="NVIDIA",
        strength="strong",
        sentiment="bullish",
        score=88,
        headline="Test headline",
        detail="Test detail",
        evidence_text="Some evidence",
    )
    assert "NVDA" in result
    assert "NVIDIA" in result
    assert "hiring_surge" in result

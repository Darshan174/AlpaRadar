"""Tests for analyzer parsing helpers."""

from src.analysis.analyzer import extract_structured_signal_analysis


def test_extract_structured_signal_analysis():
    text = """
**TLDR**: Summary

**Suggested Action**: ACCUMULATE — Demand is improving.

**Time Horizon**: MEDIUM-TERM SWING — Hiring momentum should resolve over the next quarter.

**Risk Factors**: Execution risk.

**Conviction**: HIGH BULLISH
"""

    thesis = extract_structured_signal_analysis(text)

    assert thesis is not None
    assert thesis.suggested_action == "ACCUMULATE — Demand is improving."
    assert thesis.time_horizon == "MEDIUM-TERM SWING — Hiring momentum should resolve over the next quarter."
    assert thesis.conviction == "HIGH BULLISH"

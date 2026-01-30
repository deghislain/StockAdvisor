"""Pytest configuration and fixtures for StockAdvisor tests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict

import pytest
from unittest import mock

# ----------------------------------------------------------------------
# Make the project source importable for the test session
SRC_ROOT = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(SRC_ROOT))


# ----------------------------------------------------------------------
# Helper to cleanly install a temporary stub for a module
@pytest.fixture(scope="function")
def technical_analysis_stub():
    """
    Install a lightweight ``stock_adv_technical_analysis`` stub that provides
    a ``perform_tech_analysis`` callable. The stub is removed after the test.
    """
    stub = mock.MagicMock(name="stock_adv_technical_analysis")
    stub.perform_tech_analysis = mock.MagicMock()
    sys.modules["stock_adv_technical_analysis"] = stub
    try:
        yield stub
    finally:
        # Ensure the real module (if any) can be imported later
        del sys.modules["stock_adv_technical_analysis"]


# ----------------------------------------------------------------------
# UI‑related fixture – patches Streamlit and provides a safe ``current_stock``.
@pytest.fixture
def mock_st(monkeypatch):
    """
    Patch ``src.stock_adv_user_interface.st`` (the Streamlit alias) and
    set a default ``current_stock`` attribute on the UI module.
    """
    # Import the UI module *after* the stub is in place (if needed)
    import src.ui.stock_adv_user_interface as ui

    # Replace the Streamlit object with a MagicMock
    mock_streamlit = mock.MagicMock(name="st")
    monkeypatch.setattr(ui, "st", mock_streamlit)

    yield mock_streamlit


# ----------------------------------------------------------------------
# Simple symbol fixtures
@pytest.fixture
def sample_stock_symbol() -> str:
    """A valid ticker symbol used in happy‑path tests."""
    return "IBM"


@pytest.fixture
def invalid_stock_symbol() -> str:
    """A clearly invalid ticker symbol to trigger error handling."""
    return "INVALIDSTOCK"


@pytest.fixture
def invalid_char_stock_symbol() -> str:
    """A ticker containing illegal characters (e.g., digits)."""
    return "IN1"


# ----------------------------------------------------------------------
# Generic patch‑builder – reduces duplication for the various agents
def _start_patches(patch_map: Dict[str, mock._patch]) -> Dict[str, mock.MagicMock]:
    """Start a dict of ``unittest.mock.patch`` objects and return the mocks."""
    return {name: p.start() for name, p in patch_map.items()}


def _stop_patches(patch_map: Dict[str, mock._patch]) -> None:
    """Stop all patches created by ``_start_patches``."""
    for p in patch_map.values():
        p.stop()


# ----------------------------------------------------------------------
@pytest.fixture
def patched_fin_agent_requirements():
    """
    Patch heavy dependencies of ``FinAnalystAgent``.
    Returns a mapping ``{name: mock}`` for inspection in tests.
    """
    patches = {
        "ChatModel": mock.patch("src.agents.stock_adv_analysis_engine.ChatModel"),
        "RequirementAgent": mock.patch(
            "src.agents.stock_adv_analysis_engine.RequirementAgent"
        ),
        "ThinkTool": mock.patch("src.agents.stock_adv_analysis_engine.ThinkTool"),
        "DataFetcherTool": mock.patch(
            "src.agents.stock_adv_analysis_engine.DataFetcherTool"
        ),
        "HandoffTool": mock.patch("src.agents.stock_adv_analysis_engine.HandoffTool"),
        "ConditionalRequirement": mock.patch(
            "src.agents.stock_adv_analysis_engine.ConditionalRequirement"
        ),
        "GlobalTrajectoryMiddleware": mock.patch(
            "src.agents.stock_adv_analysis_engine.GlobalTrajectoryMiddleware"
        ),
    }

    started = _start_patches(patches)
    try:
        yield started
    finally:
        _stop_patches(patches)


# ----------------------------------------------------------------------
@pytest.fixture
def patched_risk_agent_requirements():
    """
    Patch heavy dependencies of ``StockRiskAnalyzer``.
    Returns a mapping ``{name: mock}`` for inspection in tests.
    """
    patches = {
        "ChatModel": mock.patch("src.agents.stock_adv_risk_assessment.ChatModel"),
        "RequirementAgent": mock.patch(
            "src.agents.stock_adv_risk_assessment.RequirementAgent"
        ),
        "ThinkTool": mock.patch("src.agents.stock_adv_risk_assessment.ThinkTool"),
        "StockRiskAnalysisTool": mock.patch(
            "src.agents.stock_adv_risk_assessment.StockRiskAnalysisTool"
        ),
        "HandoffTool": mock.patch("src.agents.stock_adv_risk_assessment.HandoffTool"),
        "ConditionalRequirement": mock.patch(
            "src.agents.stock_adv_risk_assessment.ConditionalRequirement"
        ),
        "GlobalTrajectoryMiddleware": mock.patch(
            "src.agents.stock_adv_risk_assessment.GlobalTrajectoryMiddleware"
        ),
    }

    started = _start_patches(patches)
    try:
        yield started
    finally:
        _stop_patches(patches)


@pytest.fixture
def patched_sent_agent_requirements():
    """
    Patch heavy dependencies of ``StockMarketSentimentAnalyzer``.
    Returns a mapping ``{name: mock}`` for inspection in tests.
    """
    patches = {
        "ChatModel": mock.patch("src.agents.stock_adv_market_sentiment.ChatModel"),
        "RequirementAgent": mock.patch(
            "src.agents.stock_adv_market_sentiment.RequirementAgent"
        ),
        "ThinkTool": mock.patch("src.agents.stock_adv_market_sentiment.ThinkTool"),
        "StockRiskAnalysisTool": mock.patch(
            "src.agents.stock_adv_market_sentiment.WebSearchTool"
        ),
        "HandoffTool": mock.patch("src.agents.stock_adv_market_sentiment.HandoffTool"),
        "ConditionalRequirement": mock.patch(
            "src.agents.stock_adv_market_sentiment.ConditionalRequirement"
        ),
        "GlobalTrajectoryMiddleware": mock.patch(
            "src.agents.stock_adv_market_sentiment.GlobalTrajectoryMiddleware"
        ),
    }

    started = _start_patches(patches)
    try:
        yield started
    finally:
        _stop_patches(patches)


@pytest.fixture
def patched_report_generator_agent_requirements():
    """
    Patch heavy dependencies of ``ReportGeneratorAgent``.
    Returns a mapping ``{name: mock}`` for inspection in tests.
    """
    patches = {
        "ChatModel": mock.patch("src.agents.stock_adv_report_generator.ChatModel"),
        "RequirementAgent": mock.patch(
            "src.agents.stock_adv_report_generator.RequirementAgent"
        ),
        "ThinkTool": mock.patch("src.agents.stock_adv_report_generator.ThinkTool"),
        "HandoffTool": mock.patch("src.agents.stock_adv_report_generator.HandoffTool"),
        "ConditionalRequirement": mock.patch(
            "src.agents.stock_adv_report_generator.ConditionalRequirement"
        ),
        "GlobalTrajectoryMiddleware": mock.patch(
            "src.agents.stock_adv_report_generator.GlobalTrajectoryMiddleware"
        ),
    }

    started = _start_patches(patches)
    try:
        yield started
    finally:
        _stop_patches(patches)

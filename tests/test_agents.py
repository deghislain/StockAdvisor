"""Unit tests for StockAdvisor agents."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ----------------------------------------------------------------------
# Add src to path (kept as‑is for the original project layout)
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# ----------------------------------------------------------------------
# Optional import guard – tests are skipped if the framework is missing
try:
    import beeai_framework  # noqa: F401
    from src.stock_adv_analysis_engine import FinAnalystAgent
    from src.stock_adv_risk_assessment import StockRiskAnalyzer
    from src.stock_adv_market_sentiment import StockMarketSentimentAnalyzer

    BEEAI_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    BEEAI_AVAILABLE = False
    pytestmark = pytest.mark.skip(reason="beeai_framework not properly configured")


# ----------------------------------------------------------------------
# Simple dummy response objects – could also use SimpleNamespace
class DummyMessage:
    """Mimics `response.last_message`."""

    def __init__(self, text: str):
        self.text = text


class DummyResponse:
    """Mimics the object returned by `RequirementAgent.run`."""

    def __init__(self, text: str):
        self.last_message = DummyMessage(text)


@pytest.mark.skipif(not BEEAI_AVAILABLE, reason="Requires beeai_framework")
class TestFinAnalystAgent:
    """Test suite for the fundamental‑analysis agent."""

    @pytest.mark.asyncio
    async def test_analyze_success(
            self,
            sample_stock_symbol: str,
            patched_fin_agent_requirements: dict,
    ) -> None:
        """Agent returns a formatted analysis string for a valid symbol."""
        # Arrange ---------------------------------------------------------
        agent = FinAnalystAgent(sample_stock_symbol)

        # Mock the LLM creation
        mock_llm = MagicMock(name="DummyLLM")
        patched_fin_agent_requirements["ChatModel"].from_name.return_value = mock_llm

        # Create a chain of RequirementAgent mocks – the last one is the
        # “main” agent whose ``run`` method we actually care about.
        mock_chain = [MagicMock(name=f"Agent{i}") for i in range(5)]
        main_agent = mock_chain[-1]
        patched_fin_agent_requirements["RequirementAgent"].side_effect = mock_chain

        # Capture HandoffTool instances for optional later checks
        handoff_instances = []

        def handoff_ctor(target_agent, *, name, description):
            instance = MagicMock(name=f"Handoff({name})")
            instance.target_agent = target_agent
            instance.name = name
            instance.description = description
            handoff_instances.append(instance)
            return instance

        patched_fin_agent_requirements["HandoffTool"].side_effect = handoff_ctor

        # The main agent returns a dummy response
        dummy_resp = DummyResponse(f"Analysis for {sample_stock_symbol}")
        main_agent.run = AsyncMock(return_value=dummy_resp)

        # Act -------------------------------------------------------------
        result = await agent.analyze()

        # Assert ----------------------------------------------------------
        # The main agent must have been awaited exactly once
        main_agent.run.assert_awaited_once()

        # Result should contain the symbol and start with the dummy prefix
        assert result is not None
        assert sample_stock_symbol in result
        assert result.startswith("Analysis for")

        # Optional: verify that a HandoffTool was created for each sub‑agent
        assert len(handoff_instances) == 4  # one per non‑main agent

    @pytest.mark.asyncio
    async def test_analyze_invalid_stock_symbol(
            self,
            invalid_stock_symbol: str,
            patched_fin_agent_requirements: dict,
    ) -> None:
        """Agent returns an error message when the underlying agent raises."""
        # Arrange ---------------------------------------------------------
        agent = FinAnalystAgent(invalid_stock_symbol)

        mock_llm = MagicMock(name="DummyLLM")
        patched_fin_agent_requirements["ChatModel"].from_name.return_value = mock_llm

        # Build the same mock chain as in the success test
        mock_chain = [MagicMock(name=f"Agent{i}") for i in range(5)]
        main_agent = mock_chain[-1]
        patched_fin_agent_requirements["RequirementAgent"].side_effect = mock_chain

        # Force the main agent to raise when ``run`` is awaited
        main_agent.run = AsyncMock(side_effect=Exception("Test error"))

        # Act -------------------------------------------------------------
        result = await agent.analyze()

        # Assert ----------------------------------------------------------
        # The function should swallow the exception and return a user‑friendly
        # error string rather than propagating the exception.
        assert isinstance(result, str)
        lowered = result.lower()
        assert "error" in lowered or "unexpected" in lowered

    @pytest.mark.asyncio
    async def test_analyze_empty_response(self, sample_stock_symbol, patched_fin_agent_requirements: dict, ):
        """Test handling of empty response."""
        agent = FinAnalystAgent(sample_stock_symbol)

        mock_llm = MagicMock(name="DummyLLM")
        patched_fin_agent_requirements["ChatModel"].from_name.return_value = mock_llm

        # Build the same mock chain as in the success test
        mock_chain = [MagicMock(name=f"Agent{i}") for i in range(5)]
        main_agent = mock_chain[-1]
        patched_fin_agent_requirements["RequirementAgent"].side_effect = mock_chain

        main_agent.run = AsyncMock(return_value="")

        result = await agent.analyze()

        assert result is not None
        assert "unable" in result.lower() or "error" in result.lower()


@pytest.mark.skipif(not BEEAI_AVAILABLE, reason="Requires beeai_framework")
class TestStockRiskAnalyzer:
    """Test suite for Risk Assessment Agent."""

    @pytest.mark.asyncio
    async def test_risk_analyze_success(self, sample_stock_symbol, patched_risk_agent_requirements: dict):
        """Test risk analyzer with valid symbol."""
        analyzer = StockRiskAnalyzer(sample_stock_symbol)

        # Mock the LLM creation
        mock_llm = MagicMock(name="DummyLLM")
        patched_risk_agent_requirements["ChatModel"].from_name.return_value = mock_llm

        # Create a chain of RequirementAgent mocks – the last one is the
        # “main” agent whose ``run`` method we actually care about.
        mock_chain = [MagicMock(name=f"Agent{i}") for i in range(5)]
        main_agent = mock_chain[-1]
        patched_risk_agent_requirements["RequirementAgent"].side_effect = mock_chain

        # Capture HandoffTool instances for optional later checks
        handoff_instances = []

        def handoff_ctor(target_agent, *, name, description):
            instance = MagicMock(name=f"Handoff({name})")
            instance.target_agent = target_agent
            instance.name = name
            instance.description = description
            handoff_instances.append(instance)
            return instance

        patched_risk_agent_requirements["HandoffTool"].side_effect = handoff_ctor

        # The main agent returns a dummy response
        dummy_resp = DummyResponse(f"Risk Analysis for {sample_stock_symbol}")
        main_agent.run = AsyncMock(return_value=dummy_resp)

        result = await analyzer.analyze()

        assert result is not None
        assert sample_stock_symbol in result
        assert isinstance(result, str)

# tests/test_stock_advisors.py
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

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
    def __init__(self, text: str):
        self.text = text


class DummyResponse:
    def __init__(self, text: str):
        self.last_message = DummyMessage(text)


# ----------------------------------------------------------------------
# ── Shared fixtures ───────────────────────────────────────────────────────
@pytest.fixture
def handoff_ctor_fixture():
    """
    Returns a tuple ``(ctor, instances)`` where:

    * ``ctor`` is a callable that mimics the real ``HandoffTool`` constructor.
    * ``instances`` is the list that will contain every created mock.
    """
    instances: list[MagicMock] = []

    def handoff_ctor(target_agent, *, name, description):
        mock = MagicMock(name=f"Handoff({name})")
        mock.target_agent = target_agent
        mock.name = name
        mock.description = description
        instances.append(mock)
        return mock

    return handoff_ctor, instances


# ──────────────────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not BEEAI_AVAILABLE, reason="Requires beeai_framework")
class TestFinAnalystAgent:
    """Test suite for the fundamental‑analysis agent."""

    @pytest.mark.asyncio
    async def test_analyze_success(
            self,
            sample_stock_symbol: str,
            patched_fin_agent_requirements: dict,
            handoff_ctor_fixture,
    ) -> None:
        """Agent returns a formatted analysis string for a valid symbol."""
        # --------------------------------------------------- Arrange
        agent = FinAnalystAgent(sample_stock_symbol)

        mock_llm = MagicMock(name="DummyLLM")
        patched_fin_agent_requirements["ChatModel"].from_name.return_value = mock_llm

        # mock chain of RequirementAgent objects
        mock_chain = [MagicMock(name=f"Agent{i}") for i in range(5)]
        main_agent = mock_chain[-1]
        patched_fin_agent_requirements["RequirementAgent"].side_effect = mock_chain

        # inject shared handoff constructor
        ctor, handoff_instances = handoff_ctor_fixture
        patched_fin_agent_requirements["HandoffTool"].side_effect = ctor

        # main agent returns a dummy response
        dummy_resp = DummyResponse(f"Analysis for {sample_stock_symbol}")
        main_agent.run = AsyncMock(return_value=dummy_resp)

        result = await agent.analyze()

        main_agent.run.assert_awaited_once()
        assert isinstance(result, str)
        assert sample_stock_symbol in result
        assert result.startswith("Analysis for")
        # one HandoffTool per non‑main agent
        assert len(handoff_instances) == 4

    @pytest.mark.asyncio
    async def test_analyze_invalid_stock_symbol(
            self,
            invalid_stock_symbol: str,
            patched_fin_agent_requirements: dict,
    ) -> None:
        """Agent returns an error message when the underlying agent raises."""
        # --------------------------------------------------- Arrange
        agent = FinAnalystAgent(invalid_stock_symbol)

        mock_llm = MagicMock(name="DummyLLM")
        patched_fin_agent_requirements["ChatModel"].from_name.return_value = mock_llm

        mock_chain = [MagicMock(name=f"Agent{i}") for i in range(5)]
        main_agent = mock_chain[-1]
        patched_fin_agent_requirements["RequirementAgent"].side_effect = mock_chain

        # make the main agent raise
        main_agent.run = AsyncMock(side_effect=Exception("Test error"))

        result = await agent.analyze()

        assert isinstance(result, str)
        lowered = result.lower()
        assert "error" in lowered or "unexpected" in lowered

    @pytest.mark.asyncio
    async def test_analyze_empty_response(
            self,
            sample_stock_symbol,
            patched_fin_agent_requirements: dict,
    ):
        """Test handling of an empty response."""
        # --------------------------------------------------- Arrange
        agent = FinAnalystAgent(sample_stock_symbol)

        mock_llm = MagicMock(name="DummyLLM")
        patched_fin_agent_requirements["ChatModel"].from_name.return_value = mock_llm

        mock_chain = [MagicMock(name=f"Agent{i}") for i in range(5)]
        main_agent = mock_chain[-1]
        patched_fin_agent_requirements["RequirementAgent"].side_effect = mock_chain

        # Return a DummyResponse with an empty string (matches the real contract)
        main_agent.run = AsyncMock(return_value=DummyResponse(""))

        result = await agent.analyze()

        assert isinstance(result, str)
        assert "unable" in result.lower() or "error" in result.lower()


@pytest.mark.skipif(not BEEAI_AVAILABLE, reason="Requires beeai_framework")
class TestStockRiskAnalyzer:
    """Test suite for Risk Assessment Agent."""

    @pytest.mark.asyncio
    async def test_risk_analyze_success(
            self,
            sample_stock_symbol,
            patched_risk_agent_requirements: dict,
            handoff_ctor_fixture,
    ):
        """Test risk analyzer with a valid symbol."""
        # --------------------------------------------------- Arrange
        analyzer = StockRiskAnalyzer(sample_stock_symbol)

        mock_llm = MagicMock(name="DummyLLM")
        patched_risk_agent_requirements["ChatModel"].from_name.return_value = mock_llm

        mock_chain = [MagicMock(name=f"Agent{i}") for i in range(5)]
        main_agent = mock_chain[-1]
        patched_risk_agent_requirements["RequirementAgent"].side_effect = mock_chain

        # reuse the shared handoff constructor
        ctor, handoff_instances = handoff_ctor_fixture
        patched_risk_agent_requirements["HandoffTool"].side_effect = ctor

        dummy_resp = DummyResponse(f"Risk Analysis for {sample_stock_symbol}")
        main_agent.run = AsyncMock(return_value=dummy_resp)

        result = await analyzer.analyze()

        assert isinstance(result, str)
        assert sample_stock_symbol in result
        assert len(handoff_instances) == 3

    @pytest.mark.asyncio
    async def test_risk_analyze_invalid_stock_symbol(
            self,
            invalid_stock_symbol,
            patched_risk_agent_requirements,
    ):
        """Test error handling in risk analyzer."""
        # --------------------------------------------------- Arrange
        analyzer = StockRiskAnalyzer(invalid_stock_symbol)

        mock_llm = MagicMock(name="DummyLLM")
        patched_risk_agent_requirements["ChatModel"].from_name.return_value = mock_llm

        mock_chain = [MagicMock(name=f"Agent{i}") for i in range(5)]
        main_agent = mock_chain[-1]
        patched_risk_agent_requirements["RequirementAgent"].side_effect = mock_chain

        main_agent.run = AsyncMock(side_effect=Exception("Test error"))

        # ----------------------------------------------------- Act
        result = await analyzer.analyze()

        # ---------------------------------------------------- Assert
        assert isinstance(result, str)
        lowered = result.lower()
        assert "error" in lowered or "unexpected" in lowered

    @pytest.mark.asyncio
    async def test_risk_analyze_empty_response(
            self,
            sample_stock_symbol,
            patched_risk_agent_requirements: dict,
    ):
        """Test handling of an empty response."""
        agent = StockRiskAnalyzer(sample_stock_symbol)

        mock_llm = MagicMock(name="DummyLLM")
        patched_risk_agent_requirements["ChatModel"].from_name.return_value = mock_llm

        mock_chain = [MagicMock(name=f"Agent{i}") for i in range(5)]
        main_agent = mock_chain[-1]
        patched_risk_agent_requirements["RequirementAgent"].side_effect = mock_chain

        # Return a DummyResponse with an empty string (matches the real contract)
        main_agent.run = AsyncMock(return_value=DummyResponse(""))

        result = await agent.analyze()

        assert isinstance(result, str)
        assert "unable" in result.lower() or "error" in result.lower()

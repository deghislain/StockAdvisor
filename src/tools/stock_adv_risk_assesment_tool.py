import asyncio

import yfinance as yf
import numpy as np
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field
from beeai_framework.tools import Tool, ToolRunOptions
from beeai_framework.context import RunContext
from beeai_framework.emitter import Emitter
from beeai_framework.tools import JSONToolOutput

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class StockRiskAnalysisToolInput(BaseModel):
    """
    Input parameters for the stock‑risk‑analysis tool.

    Attributes
    ----------
    stock_symbol: str
        Ticker symbol of the target stock (e.g., "IBM ").
    benchmark_ticker: str
        Ticker of the market benchmark used for comparison. Defaults to "SPY".
    annual_risk_free_rate: float
        Annual risk‑free rate expressed as a decimal (e.g., 0.045 for 4.5%).
    """

    stock_symbol: str = Field(description="User‑provided stock symbol for risk assessment.")
    benchmark_ticker: str = Field(
        default="SPY",
        description="Benchmark ticker symbol (default: S&P 500 ETF)."
    )
    annual_risk_free_rate: float = Field(
        default=0.045,
        description="Annual risk‑free rate as a decimal (0‑1)."
    )


class StockRiskAnalysisTool(Tool[StockRiskAnalysisToolInput, ToolRunOptions, JSONToolOutput[dict[str, Any]]]):
    def __init__(self, options: dict[str, Any] | None = None) -> None:
        super().__init__(options)
        self.financials = None
        self.balance_sheet = None
        self.info = None
        self.benchmark_returns = None
        self.benchmark_data = None
        self.hist_data = None
        self.returns = None
        self.ticker = None
        self.risk_free_rate = None
        self.ticker_symbol = None

    def initialize_risk_data(self, input: StockRiskAnalysisToolInput, benchmark_ticker: str = "SPY",
                             risk_free_rate: float = 0.045):
        logging.info(f"**********************************************initialize_risk_data  START with input {input}")

        """
        Initializes the Risk Analyzer.

        Args:
            input (StockRiskAnalysisToolInput): Stock symbol (e.g., 'NVDA')
            benchmark_ticker: Market benchmark for Beta calc (default 'SPY')
            risk_free_rate: Annualized risk-free rate (decimal, e.g., 0.045 for 4.5%)
        """
        self.ticker_symbol = input.stock_symbol.upper()
        self.risk_free_rate = risk_free_rate
        self.ticker = yf.Ticker(self.ticker_symbol)

        # 1. Fetch Historical Data (Eager Loading)
        print(f"--- 📡 Fetching Data for {self.ticker_symbol} & {benchmark_ticker} ---")
        self.hist_data = self.ticker.history(period="5y", interval="1d")

        # Fetch Benchmark for Beta Calculation
        self.benchmark_data = yf.Ticker(benchmark_ticker).history(period="5y", interval="1d")

        # Align dataframes by date to ensure accurate correlation/beta
        self.hist_data, self.benchmark_data = self.hist_data.align(self.benchmark_data, join='inner', axis=0)

        # Pre-calculate returns
        self.returns = self.hist_data['Close'].pct_change().dropna()
        self.benchmark_returns = self.benchmark_data['Close'].pct_change().dropna()

        # 2. Fetch Fundamental Data
        self.info = self.ticker.info
        self.balance_sheet = self.ticker.balance_sheet
        self.financials = self.ticker.financials

    logging.info("****************************************** initialize_risk_data END********************************")

    name = "StockRiskAnalyzer"
    description = """This tool is designed to fetch data used to calculate parameters necessary 
                        for a risk assessment given a stock symbol.
      
                        Key Features:
                
                            Fetch Data: Fetch data needed to analyze market, fundamental and sentiment alternative risk, 
                            Parameters Calculation: Calculate parameters such as volatility, Beta, vaR, solvency check
                            held by insiders.
            """
    input_schema = StockRiskAnalysisToolInput

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "risk_analysis", "StockRiskAnalyzer"],
            creator=self,
        )

    async def analyze_market_risk(self) -> Dict[str, Any]:
        logging.info(f"**********************************************analyze_market_risk START***********************")
        """Calculates Volatility, Beta, VaR, and Max Drawdown."""
        if self.returns.empty:
            return {"error": "Insufficient historical data"}

        # Annualized Volatility
        volatility = self.returns.std() * np.sqrt(252)

        # Beta Calculation (Covariance / Variance)
        covariance = np.cov(self.returns, self.benchmark_returns)[0][1]
        market_variance = np.var(self.benchmark_returns)
        beta = covariance / market_variance

        # Maximum Drawdown
        cumulative = (1 + self.returns).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        max_drawdown = drawdown.min()

        # Value at Risk (VaR) - Historical Method (95% Confidence)
        # "We are 95% confident daily loss won't exceed this %"
        var_95 = np.percentile(self.returns, 5)

        # Sharpe Ratio
        excess_returns = self.returns.mean() * 252 - self.risk_free_rate
        sharpe = excess_returns / volatility if volatility != 0 else 0
        logging.info(f"**********************************************analyze_market_risk END***********************")
        return {
            "volatility_annualized": round(volatility, 4),
            "beta": round(beta, 3),
            "max_drawdown": round(max_drawdown, 4),
            "sharpe_ratio": round(sharpe, 2),
            "value_at_risk_95": round(var_95, 4),
            "risk_interpretation": self._interpret_market_risk(beta, volatility)
        }

    async def analyze_fundamental_risk(self) -> Dict[str, Any]:
        """Analyzes Solvency and Liquidity risks from Balance Sheet/Income Stmt."""
        logging.info(f"*************************************analyze_fundamental_risk START***********************")
        try:
            # Get most recent reporting period
            bs = self.balance_sheet.iloc[:, 0] if not self.balance_sheet.empty else None
            is_stmt = self.financials.iloc[:, 0] if not self.financials.empty else None

            if bs is None or is_stmt is None:
                return {"error": "Missing financial statements"}

            # Solvency: Debt to Equity
            total_debt = bs.get('Total Debt', 0)
            total_equity = bs.get('Stockholders Equity', 1)  # Avoid div/0
            debt_to_equity = total_debt / total_equity

            # Liquidity: Current Ratio (Assets / Liabilities)
            curr_assets = bs.get('Current Assets', 0)
            curr_liab = bs.get('Current Liabilities', 1)
            current_ratio = curr_assets / curr_liab

            # Coverage: Interest Coverage (EBIT / Interest Expense)
            ebit = is_stmt.get('EBIT', 0)
            interest = abs(is_stmt.get('Interest Expense', 0))
            interest_coverage = ebit / interest if interest > 0 else 999.0  # 999 implies safe/no interest
            logging.info(
                f"**********************************************analyze_fundamental_risk END***********************")
            return {
                "debt_to_equity": round(debt_to_equity, 2),
                "current_ratio": round(current_ratio, 2),
                "interest_coverage": round(interest_coverage, 2),
                "solvency_check": "High Risk" if debt_to_equity > 2.0 else "Stable"
            }
        except Exception as e:
            return {"error": f"Fundamental calculation failed: {str(e)}"}

    async def analyze_sentiment_alternative_risk(self) -> Dict[str, Any]:
        """Analyzes Short Interest and Implied Volatility."""
        logging.info(f"*******************************analyze_sentiment_alternative_risk START***********************")
        # Short Interest
        short_percent = self.info.get('shortPercentOfFloat', 0)

        # Implied Volatility (Using 52Week Change as a crude proxy if Option chain fails,
        # or checking info dict which sometimes has 'impliedVolatility')
        # Note: Accurate IV requires option chain iteration, we use 'beta' as proxy for expectation here
        # or relying on yfinance info if available.
        logging.info(f"*******************************analyze_sentiment_alternative_risk END***********************")
        return {
            "short_percent_of_float": round(short_percent, 4) if short_percent else "N/A",
            "held_by_insiders": round(self.info.get('heldPercentInsiders', 0), 4),
            "short_squeeze_risk": "High" if (short_percent and short_percent > 0.15) else "Low"
        }

    def _interpret_market_risk(self, beta: float, vol: float) -> str:
        """Helper to generate a human-readable risk summary."""
        logging.info(f"*************************************_interpret_market_risk START***********************")
        interpretation = []
        if beta > 1.5:
            interpretation.append("Highly Volatile (High Beta)")
        elif beta < 0.8:
            interpretation.append("Defensive/Low Correlation")

        if vol > 0.50:  # >50% annualized volatility
            interpretation.append("Extreme Price Swings")
        logging.info(f"***********************_interpret_market_risk END with interpretation ***********************")
        return " & ".join(interpretation) if interpretation else "Moderate Market Risk"

    async def generate_full_report(self) -> Dict[str, Any]:
        """Aggregates all risk modules into a final report."""
        logging.info(f"*************************************generate_full_report START***********************")
        return {
            "ticker": self.ticker_symbol,
            "timestamp": datetime.now().isoformat(),
            "market_risk": await self.analyze_market_risk(),
            "fundamental_risk": await self.analyze_fundamental_risk(),
            "sentiment_risk": await self.analyze_sentiment_alternative_risk()
        }

    async def _run(
            self,
            input: StockRiskAnalysisToolInput,
            options: ToolRunOptions | None,
            context: RunContext,
    ) -> JSONToolOutput[dict[str, Any]]:
        StockRiskAnalysisTool.initialize_risk_data(self, input)

        output = await StockRiskAnalysisTool.generate_full_report(self)
        print(output)
        if output:
            return JSONToolOutput(output)


# ==========================================
# Example Usage
# ==========================================
async def main() -> None:
    try:
        tool = StockRiskAnalysisTool()
        input = StockRiskAnalysisToolInput(stock_symbol="IBM")
        output = await tool.run(input)
        print("**********************************")
        logging.info(output.result.get('market_risk'))
        logging.info(output.result.get('fundamental_risk'))
        logging.info(output.result.get('sentiment_risk'))
        '''
        #print(output.result.get('market_risk'))
        print("\n" + "=" * 60)
        print(f"🚨 RISK ANALYSIS REPORT: {output['ticker']}")
        print("=" * 60)

        mr = output['market_risk']
        print(f"\n📉 MARKET RISK (Quant):")
        print(f"   • Beta: {mr['beta']} (vs SPY)")
        print(f"   • Annual Volatility: {mr['volatility_annualized'] * 100}%")
        print(f"   • Max Drawdown (5Y): {mr['max_drawdown'] * 100}%")
        print(f"   • Value at Risk (95% Daily): {mr['value_at_risk_95'] * 100}%")
        print(f"   • Interpretation: {mr['risk_interpretation']}")

        fr = output['fundamental_risk']
        print(f"\n🏢 FUNDAMENTAL RISK (Solvency/Liquidity):")
        print(f"   • Debt-to-Equity: {fr.get('debt_to_equity', 'N/A')} (Target < 2.0)")
        print(f"   • Current Ratio: {fr.get('current_ratio', 'N/A')} (Target > 1.0)")
        print(f"   • Interest Coverage: {fr.get('interest_coverage', 'N/A')}x")

        sr = output['sentiment_risk']
        print(f"\n🐻 SENTIMENT/ALTERNATIVE RISK:")
        print(f"   • Short Interest: {float(sr.get('short_percent_of_float', 0)) * 100}%")
        print(f"   • Insider Ownership: {float(sr.get('held_by_insiders', 0)) * 100}%")
        print(f"   • Squeeze Risk: {sr['short_squeeze_risk']}")
        '''
    except Exception as e:
        print(f"Analysis failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())

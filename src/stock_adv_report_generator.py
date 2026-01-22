"""Creates detailed reports based on the fetched data.
    The ReportGenerator compiles all the information, including data analysis, market sentiment, risk assessment,
     and the recommendation, into a comprehensive report.
    This report is formatted for easy reading and includes visual aids like charts and graphs.
"""

from beeai_framework.agents.requirement import RequirementAgent
from beeai_framework.tools.handoff import HandoffTool
from beeai_framework.backend import ChatModel
from beeai_framework.tools.think import ThinkTool
from beeai_framework.agents.requirement.requirements.conditional import ConditionalRequirement
from beeai_framework.middleware.trajectory import GlobalTrajectoryMiddleware
from beeai_framework.tools import Tool
from beeai_framework.errors import FrameworkError

import asyncio, logging, time
from typing import Any

from stock_adv_analysis_engine import FinAnalystAgent
from stock_adv_market_sentiment import StockMarketSentimentAnalyzer
from stock_adv_risk_assessment import StockRiskAnalyzer
from config import ModelConfig as mc
from stock_adv_report_instructions import REPORT_WRITER_INSTRUCTIONS, REPORT_REVIEWER_INSTRUCTIONS, REPORT_REFINER_INSTRUCTIONS
from stock_adv_prompts import get_final_report_prompt

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class ReportGeneratorAgent:
    def __init__(self, stock_symbol: str):
        self.fin_analyst_agent = FinAnalystAgent(stock_symbol)
        self.market_sentiment_analyzer = StockMarketSentimentAnalyzer(stock_symbol)
        self.risk_assessment_agent = StockRiskAnalyzer(stock_symbol)

        self.fund_analysis = None
        self.market_sentiment_analysis = None
        self.stock_symbol = stock_symbol
        self.generated_report = None
        self.report_queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()

    async def _perform_fundamental_analysis(self, ):
        logging.info(f"[FUNDAMENTAL] Starting analysis for {self.stock_symbol}")
        start_time = time.time()
        
        try:
            if self.stock_symbol:
                self.fund_analysis = await self.fin_analyst_agent.analyze()
                if self.fund_analysis:
                    await self.report_queue.put(("fund_analysis", self.fund_analysis))
                    duration = time.time() - start_time
                    logging.info(f"[FUNDAMENTAL] Completed successfully in {duration:.2f}s for {self.stock_symbol}")
                else:
                    logging.warning(f"[FUNDAMENTAL] Empty result for {self.stock_symbol}")
                    await self.report_queue.put(("fund_analysis", f"Unable to complete fundamental analysis for {self.stock_symbol}"))
        except Exception as e:
            duration = time.time() - start_time
            logging.error(f"[FUNDAMENTAL] Failed after {duration:.2f}s for {self.stock_symbol}: {e}", exc_info=True)
            await self.report_queue.put(("fund_analysis", f"Fundamental analysis error: {str(e)}"))

    async def _perform_market_sentiment_analysis(self, ):
        logging.info(f"[SENTIMENT] Starting analysis for {self.stock_symbol}")
        start_time = time.time()
        
        try:
            if self.stock_symbol:
                self.market_sentiment_analysis = await self.market_sentiment_analyzer.analyze()
                if self.market_sentiment_analysis:
                    await self.report_queue.put(("market_sent_analysis", self.market_sentiment_analysis))
                    duration = time.time() - start_time
                    logging.info(f"[SENTIMENT] Completed successfully in {duration:.2f}s for {self.stock_symbol}")
                else:
                    logging.warning(f"[SENTIMENT] Empty result for {self.stock_symbol}")
                    await self.report_queue.put(("market_sent_analysis", f"Unable to complete sentiment analysis for {self.stock_symbol}"))
        except Exception as e:
            duration = time.time() - start_time
            logging.error(f"[SENTIMENT] Failed after {duration:.2f}s for {self.stock_symbol}: {e}", exc_info=True)
            await self.report_queue.put(("market_sent_analysis", f"Sentiment analysis error: {str(e)}"))

    async def _perform_risk_assessment(self, ):
        logging.info(f"[RISK] Starting analysis for {self.stock_symbol}")
        start_time = time.time()
        
        try:
            if self.stock_symbol:
                self.risk_assessment = await self.risk_assessment_agent.analyze()
                if self.risk_assessment:
                    await self.report_queue.put(("risk_assessment", self.risk_assessment))
                    duration = time.time() - start_time
                    logging.info(f"[RISK] Completed successfully in {duration:.2f}s for {self.stock_symbol}")
                else:
                    logging.warning(f"[RISK] Empty result for {self.stock_symbol}")
                    await self.report_queue.put(("risk_assessment", f"Unable to complete risk assessment for {self.stock_symbol}"))
        except Exception as e:
            duration = time.time() - start_time
            logging.error(f"[RISK] Failed after {duration:.2f}s for {self.stock_symbol}: {e}", exc_info=True)
            await self.report_queue.put(("risk_assessment", f"Risk assessment error: {str(e)}"))

    async def _write_final_report(self, initial_report: str) -> str:
        logging.info(f"******************************_write_final_report STARTS with input: {initial_report} *******///")
        report_writer = RequirementAgent(
            llm=ChatModel.from_name(mc.small_model, timeout=mc.llm_timeout, stream=False),
            tools=[ThinkTool(), ],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
            role="Report Writer",
            instructions=REPORT_WRITER_INSTRUCTIONS,
        )
        report_reviewer = RequirementAgent(
            llm=ChatModel.from_name(mc.fin_model, timeout=mc.llm_timeout, stream=False),
            tools=[ThinkTool(), ],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
            role="Report Reviewer",
            instructions=REPORT_REVIEWER_INSTRUCTIONS,
        )
        report_refiner = RequirementAgent(
            llm=ChatModel.from_name(mc.small_model, timeout=mc.llm_timeout, stream=False),
            tools=[ThinkTool(), ],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
            role="Report Refiner",
            instructions=REPORT_REFINER_INSTRUCTIONS,
        )

        main_agent = RequirementAgent(
            name="MainAgent",
            llm=ChatModel.from_name(mc.small_model, timeout=mc.main_llm_timeout, stream=False),
            tools=[
                ThinkTool(),
                HandoffTool(
                    report_writer,
                    name="ReportWriting",
                    description="Consult the Report Writer Agent for report writing.",
                ),
                HandoffTool(
                    report_reviewer,
                    name="ReportReview",
                    description="Consult the Report Reviewer Agent for report review.",
                ),
                HandoffTool(
                    report_refiner,
                    name="ReportEnhancement",
                    description="Consult the Report Refiner Agent for report refinement and improvement.",
                ),

            ],
            requirements=[ConditionalRequirement(ThinkTool, force_at_step=1)],
            # Log all tool calls to the console for easier debugging
            middlewares=[GlobalTrajectoryMiddleware(included=[Tool])],
        )
        prompt = get_final_report_prompt(initial_report)
        agent_response = None
        
        try:
            response = await main_agent.run(prompt, expected_output="Helpful and clear response.")
            
            # Safely extract the response
            if response and hasattr(response, 'last_message') and hasattr(response.last_message, 'text'):
                final_report = response.last_message.text
                
                if final_report:
                    agent_response = final_report
                    logging.info("Final report generation completed successfully")
                else:
                    logging.warning("Empty final report generated")
                    agent_response = "Unable to generate final report. Please try again."
            else:
                logging.error("Unexpected response structure from report writer agent")
                agent_response = "Technical error occurred during report generation."
                
        except FrameworkError as err:
            error_msg = f"Framework error in report generation: {err.explain()}"
            logging.error(error_msg, exc_info=True)
            agent_response = "Report generation framework error. Please try again later."
            
        except AttributeError as err:
            logging.error(f"Response structure error in report generation: {err}", exc_info=True)
            agent_response = "Data structure error during report generation."
            
        except Exception as err:
            logging.error(f"Unexpected error in report generation: {err}", exc_info=True)
            agent_response = "Unexpected error occurred during report generation."
            
        logging.info(f"_write_final_report completed with result: {bool(agent_response)}")
        return agent_response

    async def generate_report(self, ):
        """
        Generate a comprehensive stock report by running all analyses concurrently.
        
        Returns:
            str: The generated report or error message
        """
        logging.info(f"Starting report generation for: {self.stock_symbol}")
        
        try:
            tasks = [
                asyncio.create_task(self._perform_fundamental_analysis()),
                asyncio.create_task(self._perform_market_sentiment_analysis()),
                asyncio.create_task(self._perform_risk_assessment())
            ]

            # Wait for all results (order depends on which task finishes first)
            results: dict[str, Any] = {}
            for i in range(3):
                try:
                    logging.info(f"Waiting for analysis result {i+1}/3...")
                    kind, payload = await asyncio.wait_for(
                        self.report_queue.get(), 
                        timeout=mc.default_timeout  # 10 minutes timeout per analysis
                    )
                    logging.info(f"[QUEUE] Received result {i+1}/3: {kind}")
                    results[kind] = payload
                except asyncio.TimeoutError:
                    logging.error(f"[QUEUE] Timeout waiting for analysis result {i+1}/3 after 600 seconds")
                    logging.error(f"[QUEUE] Results received so far: {list(results.keys())}")
                    return f"Report generation timed out for {self.stock_symbol}. One or more analyses took longer than 10 minutes. Please try again."
                    
            # Ensure all tasks complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Validate we have all required results
            required_keys = ["fund_analysis", "market_sent_analysis", "risk_assessment"]
            missing_keys = [key for key in required_keys if key not in results]
            
            if missing_keys:
                logging.error(f"Missing analysis results: {missing_keys}")
                return f"Incomplete analysis for {self.stock_symbol}. Missing: {', '.join(missing_keys)}"
            
            # Combine all analyses
            separator = "\n\n\n"
            initial_report = separator.join([
                results["fund_analysis"], 
                results["market_sent_analysis"],
                results["risk_assessment"]
            ])
            
            if initial_report and initial_report.strip():
                self.generated_report = await self._write_final_report(initial_report)
                
                if self.generated_report:
                    logging.info(f"Report generation completed successfully for {self.stock_symbol}")
                    self.report_queue.task_done()
                    return self.generated_report
                else:
                    logging.error("Final report generation failed")
                    return f"Failed to generate final report for {self.stock_symbol}."
            else:
                logging.error("Initial report is empty")
                return f"Unable to compile analysis data for {self.stock_symbol}."
                
        except Exception as err:
            logging.error(f"Unexpected error in generate_report for {self.stock_symbol}: {err}", exc_info=True)
            return f"An unexpected error occurred while generating the report for {self.stock_symbol}. Please try again."


async def main():
    report_agent = ReportGeneratorAgent("IBM")
    generated_report = await report_agent.generate_report()
    if generated_report:
        logging.info(f"******************************----****generate_report result: {generated_report}")


if __name__ == "__main__":
    asyncio.run(main())

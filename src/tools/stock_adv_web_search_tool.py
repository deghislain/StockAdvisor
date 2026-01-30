import asyncio
from pydantic import BaseModel, Field
from beeai_framework.tools import StringToolOutput, Tool, ToolRunOptions
from beeai_framework.emitter import Emitter
from beeai_framework.context import RunContext
from typing import Dict, Any, Optional
from io import StringIO

import logging

from tools.stock_adv_web_scraping import ContentExtractor
from tools.stock_adv_web_search import NewsSearcher

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class StockIntelParser:
    """Parser for stock intelligence data with proper formatting and validation."""

    # Class constants for formatting (maintainability)
    SECTION_SEPARATOR = "=" * 60
    SUBSECTION_SEPARATOR = "-" * 50
    ICONS = {
        "report": "📊",
        "news": "📰",
        "social": "💬",
        "source": "📎"
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize with optional logger for dependency injection."""
        self.logger = logger or logging.getLogger(__name__)

    def _get_url_content(self, current_url: str):
        """
           Fetch the main textual content of *current_url*.

           Parameters
           ----------
           current_url : str
               The URL to scrape. Must be a non‑empty string.

           Returns
           -------
           str
               Extracted content; empty string if extraction fails.

           Raises
           ------
           ValueError
               If ``current_url`` is falsy.
        """
        if not current_url:
            raise ValueError("All parameters (current_url) must be provided.")

        new_content = ""
        cont_extractor = ContentExtractor()
        content, error = cont_extractor.extract(current_url)
        if content:
            new_content += content
        if error:
            logging.error(f"Content extraction failed for %s – %s {current_url}, {error}")
        else:
            logging.warning(f"Extractor returned no content for %s {current_url}")
        if new_content:
            return new_content
        else:
            return ""

    @staticmethod
    def _validate_intel_structure(data: Dict[str, Any], expected_ticker: str) -> None:
        """
        Validate collected_intel structure before processing.
        Raises ValueError with specific message if invalid.
        """
        required_keys = {'ticker', 'timestamp', 'news', 'social'}
        missing_keys = required_keys - data.keys()

        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")

        if not isinstance(data['news'], list) or not isinstance(data['social'], list):
            raise ValueError("news and social must be lists")

        if data['ticker'] != expected_ticker:
            raise ValueError(f"Ticker mismatch: expected '{expected_ticker}', got '{data['ticker']}'")

    def _format_article(self, idx: int, article: Dict[str, Any]) -> str:
        """Format a single news article entry."""
        title = article.get('title', 'No title')
        source = article.get('source', 'Unknown')
        date = article.get('date', 'N/A')
        url = article.get('url', '')

        return (
            f"\n{idx}. {title}\n"
            f"   {self.ICONS['source']} Source: {source} ({date})\n"
            f"{self._get_url_content(url)}"
        )

    def _format_social_post(self, idx: int, post: Dict[str, Any]) -> str:
        """Format a single social media post entry."""
        platform = post.get('platform', 'Unknown')
        title = post.get('title', 'No title')
        url = post.get('url', '')

        return (
            f"\n{idx}. [{platform}] {title}\n"
            f"{self._get_url_content(url)}"
        )

    def parse_intelligence(self, ticker: str, collected_intel: Dict[str, Any]) -> str:
        """
        Parse collected stock intelligence into a formatted report.

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')
            collected_intel: Dictionary with ticker, timestamp, news, and social data

        Returns:
            Formatted multi-line string report

        Raises:
            ValueError: If input parameters are invalid or data structure is malformed
        """
        # Early validation for fail-fast behavior
        if not ticker or not collected_intel:
            raise ValueError("Both 'ticker' and 'collected_intel' must be provided")

        self._validate_intel_structure(collected_intel, ticker)

        # Use StringIO for O(n) string building performance
        output = StringIO()

        try:
            # Header section
            output.write(
                f"Generating intelligence report for ${ticker}...\n"
                f"{self.SECTION_SEPARATOR}\n"
                f"{self.ICONS['report']} STOCK INTELLIGENCE REPORT: {collected_intel['ticker']}\n"
                f"Generated: {collected_intel['timestamp']}\n"
                f"{self.SECTION_SEPARATOR}\n\n"
            )

            # News section
            news_articles = collected_intel.get('news', [])
            output.write(f"{self.ICONS['news']} FINANCIAL NEWS ({len(news_articles)} articles)\n")
            output.write(f"{self.SUBSECTION_SEPARATOR}\n")

            for idx, article in enumerate(news_articles, 1):
                if article:  # Skip empty dicts
                    output.write(self._format_article(idx, article))

            # Social section
            social_posts = collected_intel.get('social', [])
            output.write(f"\n{self.ICONS['social']} SOCIAL MEDIA DISCUSSIONS ({len(social_posts)} posts)\n")
            output.write(f"{self.SUBSECTION_SEPARATOR}\n")

            for idx, post in enumerate(social_posts, 1):
                if post:  # Skip empty dicts
                    output.write(self._format_social_post(idx, post))

            output.write(f"{self.SECTION_SEPARATOR}\n")

        except KeyError as e:
            self.logger.error(f"Malformed data structure: missing key {e}")
            raise ValueError(f"Invalid data structure: missing key {e}") from e
        except Exception as e:
            self.logger.exception("Unexpected error during report generation")
            raise  # Re-raise to let caller decide how to handle

        return output.getvalue()


class WebSearchToolInput(BaseModel):
    query: str = Field(description="""User input query for conducting an internet search. This query can include keywords, 
    phrases, or specific questions that the user wants to find information about online.""")


class WebSearchTool(Tool[WebSearchToolInput, ToolRunOptions, StringToolOutput]):
    name = "websearcher"
    description = """This tool is designed to search for and retrieve online trends, news, current events, 
    real-time information, or research topics. It has the capability to scrape the content of URLs within 
    the search results, allowing for in-depth analysis and summarization of the information found.

    Key Features:
    
        Search Capabilities: Perform searches across a wide range of topics, including trends, news, current events, 
        real-time information, and research topics.
        Content Scraping: Extract and scrape the content from URLs within the search results, enabling detailed 
        examination of the information.
        Real-Time Data: Access up-to-date information to ensure the most current and relevant data is retrieved.
        Comprehensive Results: Retrieve a broad spectrum of results to provide a thorough understanding of the search query.

    """
    input_schema = WebSearchToolInput

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        super().__init__(options)

    def _create_emitter(self) -> Emitter:
        return Emitter.root().child(
            namespace=["tool", "search_scrap", "websearcher"],
            creator=self,
        )

    async def _run(
            self, input: WebSearchToolInput, options: ToolRunOptions | None, context: RunContext
    ) -> StringToolOutput:
        """
           Asynchronously searches for news articles related to the input query and extracts content from each URL.

           Parameters:
           - input (WebSearchToolInput): The search input containing the query.
           - options (ToolRunOptions | None): Optional run options.
           - context (RunContext): The run context.

           Returns:
           - List[str]: A list of extracted article contents.

           """
        if not input:
            raise ValueError("All parameters (ticker) must be provided.")

        logging.info(f"*********************get_latest_news START with input query: {input.query}")
        news_searcher = NewsSearcher()
        news_content = ""
        try:

            news_result = news_searcher.search(input.query, limit=4)

            parser = StockIntelParser()
            news_content = parser.parse_intelligence(input.query, news_result)
        except Exception as e:
            logging.error(f"An error occurred: {e}")
        return StringToolOutput(news_content)


async def main() -> None:
    tool = WebSearchTool()
    query = "What is the current price for IBM stock?"
    input = WebSearchToolInput(query="IBM")
    contents = await tool.run(input)
    logging.info(f"///////////////////////////////{contents}")


if __name__ == "__main__":
    asyncio.run(main())

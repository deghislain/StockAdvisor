from typing import Any
import asyncio
from pydantic import BaseModel, Field
from beeai_framework.tools import StringToolOutput, Tool, ToolRunOptions
from beeai_framework.emitter import Emitter
from beeai_framework.context import RunContext
from stock_adv_web_scraping import ContentExtractor
import logging

from stock_adv_web_search import NewsSearcher

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


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
        extracted_content = ""
        logging.info(f"*********************get_latest_news START with input query: {input.query}")
        news = NewsSearcher()
        cont_extractor = ContentExtractor()

        try:
            news_result = news.search(input.query, max_results=5)

            for i, item in enumerate(news_result, start=1):
                current_url = item['url']
                new_content = "\n###########################################################################################\n"
                content, error = cont_extractor.extract(current_url)
                if content:
                    new_content += content
                if error:
                    logging.error(f"❌ {error}")
                else:
                    logging.debug("✅ Extracted content (first 1000 characters):")
                    extracted_content += new_content

        except Exception as e:
            logging.error(f"An error occurred: {e}")
        return StringToolOutput(extracted_content)


async def main() -> None:
    tool = WebSearchTool()
    query = "What is the current price for IBM stock?"
    input = WebSearchToolInput(query=query)
    contents = await tool.run(input)
    logging.info(f"///////////////////////////////{contents}")


if __name__ == "__main__":
    asyncio.run(main())

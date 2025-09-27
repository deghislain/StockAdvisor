from ddgs import DDGS
from typing import List, Dict
import logging
from langchain_community.tools import DuckDuckGoSearchRun

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class NewsSearcher:
    """
    A small class that queries DuckDuckGo’s *news* vertical.

    Example
    -------
    >>> client = NewsSearcher()
    >>> articles = client.search("space tourism", max_results=5)
    >>> for a in articles:
    ...     print(a["title"])
    """

    def __init__(self,
                 region: str = "wt-wt",
                 safesearch: str = "On"):
        """
        Parameters
        ----------
        region: str
            DDG region code (default “wt-wt” – worldwide).
        safesearch: str
            One of “Off”, “Moderate”, or “Strict”.
        """
        self.region = region
        self.safesearch = safesearch

    def _format_result(self, raw: Dict) -> Dict:
        logging.info("*********************_format_result START")
        """Extract the fields we care about from a raw DDGS result."""
        return {
            "title": raw.get("title"),
            "url": raw.get("url"),
            "source": raw.get("source"),
            "date": raw.get("date"),
            "snippet": raw.get("body")
        }

    def search(self,
               topic: str,
               max_results: int = 10) -> List[Dict]:
        logging.info(f"*********************search START with input: {topic}")
        """
        Query DuckDuckGo news and return a list of article dictionaries.

        Parameters
        ----------
        topic: str
            Search term, e.g. “artificial intelligence”.
        max_results: int, optional
            Upper bound on the number of articles returned (default 10).

        Returns
        -------
        List[Dict]
            Each dict contains ``title``, ``url``, ``source``, ``date`` and
            ``snippet``.
        """
        results: List[Dict] = []

        # DDGS strips identifying metadata before the request is sent.

        with DDGS() as ddgs:
            for raw in ddgs.news(topic,
                                 region=self.region,
                                 safesearch=self.safesearch):
                results.append(self._format_result(raw))
                if len(results) >= max_results:
                    break

        search = DuckDuckGoSearchRun()

        additional_info = search.invoke(topic)
        results.append(additional_info)
        logging.info(f"*********************search ENDED Successfully additional_info = {additional_info}")
        return results


# ----------------------------------------------------------------------
# Example usage
if __name__ == "__main__":
    query = "What is the current IBM stock price"
    client = NewsSearcher()
    #get_latest_news(query)

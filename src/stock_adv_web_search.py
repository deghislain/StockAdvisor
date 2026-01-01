from duckduckgo_search import DDGS
from typing import Dict, List, Any
from datetime import datetime

import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class NewsSearcher:
    """A small class that queries DuckDuckGo’s *news* vertical."""

    def search(self, ticker: str, limit: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Collects recent news articles, social media posts, and opinions for a given stock.
        Uses DuckDuckGo search engine as an aggregator (no API key required).

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA', 'TSLA', 'AAPL')
            limit: Maximum number of results per category (default: 5)

        Returns:
            Dictionary containing:
            - 'news': Recent financial news articles
            - 'social': Social media posts and forum discussions
        """
        logging.info(f"************************search start with input: {ticker}*****************")
        report = {
            "ticker": ticker.upper(),
            "timestamp": datetime.now().isoformat(),
            "news": [],
            "social": []
        }

        with DDGS() as ddgs:  # Context manager ensures proper session handling

            # 1. Official News (High Credibility)
            # Using .news() for structured news results with source attribution
            try:
                news_results = ddgs.news(
                    keywords=f"{ticker} stock",
                    region="us-en",
                    max_results=limit
                )

                for item in news_results:
                    report["news"].append({
                        "title": item.get("title", ""),
                        "source": item.get("source", "Unknown"),
                        "date": item.get("date", "N/A"),
                        "url": item.get("url", ""),
                        "snippet": item.get("body", "")[:200] + "..."
                    })
            except Exception as e:
                print(f"⚠️ News retrieval failed: {e}")

            # 2. Social Media & Forum Discussions
            # Using .text() with site: operators to target social platforms
            # This aggregates Reddit, StockTwits, and Twitter without needing their APIs
            try:
                social_query = f'{ticker} stock (site:reddit.com OR site:stocktwits.com OR site:twitter.com)'
                social_results = ddgs.text(
                    keywords=social_query,
                    region="wt-wt",
                    max_results=limit
                )

                for item in social_results:
                    # Determine platform from URL
                    url = item.get("href", "")
                    if "reddit.com" in url:
                        platform = "Reddit"
                    elif "stocktwits.com" in url:
                        platform = "StockTwits"
                    elif "twitter.com" in url:
                        platform = "Twitter"
                    else:
                        platform = "Forum"

                    report["social"].append({
                        "platform": platform,
                        "title": item.get("title", "Discussion"),
                        "url": url,
                        "snippet": item.get("body", "")[:150] + "..."
                    })
            except Exception as e:
                print(f"⚠️ Social retrieval failed: {e}")

        return report


if __name__ == "__main__":
    target_ticker = "NVDA"

    logging.info(f"Generating intelligence report for ${target_ticker}...\n")
    news_searcher = NewsSearcher()
    intel = news_searcher.search(target_ticker, limit=4)

    # Display Results
    logging.info("=" * 60)
    logging.info(f"📊 STOCK INTELLIGENCE REPORT: {intel['ticker']}")
    logging.info(f"Generated: {intel['timestamp']}")
    logging.info("=" * 60)

    logging.info(f"\n📰 FINANCIAL NEWS ({len(intel['news'])} articles)")
    logging.info("-" * 50)
    for idx, article in enumerate(intel['news'], 1):
        logging.info(f"\n{idx}. {article['title']}")
        logging.info(f"   📎 Source: {article['source']} ({article['date']})")
        logging.info(f"   🌐 {article['url']}")
        logging.info(f"   📝 {article['snippet']}")

    logging.info(f"\n💬 SOCIAL MEDIA DISCUSSIONS ({len(intel['social'])} posts)")
    logging.info("-" * 50)
    for idx, post in enumerate(intel['social'], 1):
        logging.info(f"\n{idx}. [{post['platform']}] {post['title']}")
        logging.info(f"   🔗 {post['url']}")
        logging.info(f"   💭 {post['snippet']}")
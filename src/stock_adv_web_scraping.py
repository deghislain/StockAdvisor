import requests
from bs4 import BeautifulSoup
from typing import Tuple, Optional
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class ContentExtractor:
    """
    A reusable helper for downloading a URL and pulling out the most relevant
    article‑style text.

    Example
    -------
    >>> extractor = ContentExtractor()
    >>> text, err = extractor.extract("https://example.com/blog/post")
    >>> if err:
    ...     print(err)
    ... else:
    ...     print(text[:200])
    """

    def __init__(self,
                 timeout: int = 10,
                 user_agent: str = "Mozilla/5.0"):
        """
        Parameters
        ----------
        timeout: int
            Seconds to wait for the HTTP request (default 10).
        user_agent: str
            Header sent with the request to avoid trivial blocks.
        """
        self.timeout = timeout
        self.headers = {"User-Agent": user_agent}

    def _fetch_page(self, url: str) -> Tuple[Optional[bytes], Optional[str]]:
        logging.info(f"*********************_fetch_page START with input {url}")
        """
        Download raw HTML from *url*.

        Returns (content, error):
            *content* – response body as bytes or ``None`` on failure.
            *error*   – error message or ``None`` on success.
        """
        try:
            resp = requests.get(url,
                                timeout=self.timeout,
                                headers=self.headers)
            resp.raise_for_status()
            return resp.content, None
        except requests.RequestException as exc:
            logging.info(f"*********************_fetch_page ENDED Successfully")
            return None, str(exc)

    def _extract_main_text(self, html: bytes) -> str:
        logging.info(f"*********************_extract_main_text START")
        """
        Parse *html* with BeautifulSoup and return the most relevant text.

        Heuristic steps:
            1. Remove scripts, styles, navigation, etc.
            2. Prefer an <article> element if present.
            3. Otherwise pick the largest <div>/<section> by character count.
        """
        soup = BeautifulSoup(html, "html.parser")

        # Strip noisy tags
        for tag in soup(["script", "style", "noscript",
                         "header", "footer", "nav", "aside"]):
            tag.decompose()

        article = soup.find("article")
        if article:
            logging.info(f"*********************_extract_main_text ENDED Successfully")
            return article.get_text(separator="\n", strip=True)

        candidates = soup.find_all(["div", "section"], recursive=True)
        best_text, max_len = "", 0
        for cand in candidates:
            txt = cand.get_text(separator="\n", strip=True)
            if len(txt) > max_len:
                best_text, max_len = txt, len(txt)
        logging.info(f"*********************_fetch_page ENDED Successfully")
        return best_text

    def extract(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        logging.info(f"*********************extract START with input {url}")
        """
        Download *url* and return cleaned textual content.

        Returns (text, error):
            *text* – extracted article body or ``None`` on failure.
            *error* – description of what went wrong, or ``None`` on success.
        """
        html, fetch_err = self._fetch_page(url)
        if fetch_err:
            return None, f"Download error: {fetch_err}"

        try:
            text = self._extract_main_text(html)
            if not text:
                return None, "No extractable text found."
            return text, None
        except Exception as exc:  # pragma: no cover
            return None, f"Parsing error: {exc}"


# ----------------------------------------------------------------------
# Example usage
if __name__ == "__main__":
    extractor = ContentExtractor()
    url = "https://finance.yahoo.com/news/ibm-ibm-crossed-above-200-133001712.html"
    content, error = extractor.extract(url)

    if error:
        print(f"❌ {error}")
    else:
        print("✅ Extracted content (first 300 characters):")
        print(content[:1000] + ("…" if len(content) > 1000 else ""))

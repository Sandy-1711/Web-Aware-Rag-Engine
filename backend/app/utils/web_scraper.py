import trafilatura
from typing import Dict
import logging
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
logger = logging.getLogger(__name__)


class WebScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def scrape_url(self, url: str) -> Dict[str, str]:
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            content = trafilatura.extract(
                response.content,
                include_links=False,
                include_images=False,
                include_tables=True,
            )
            if not content:
                content = self._fallback_extraction(response.content)

            title = self._extract_title(response.content)

            if not content or len(content.strip()) < 100:
                raise ValueError("Insufficient content extracted from URL")

            logger.info(f"Successfully scraped URL: {url} (length: {len(content)})")
            return {"content": content, "title": title, "url": url}

        except requests.RequestException as e:
            logger.error(f"Failed to fetch URL: {str(e)}")
            raise ValueError(f"Request error: {e}")
        except Exception as e:
            logger.error(f"Error scraping url: {e}")
            raise


scraper = WebScraper()

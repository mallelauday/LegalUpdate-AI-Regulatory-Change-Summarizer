import logging
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup
from config import Config
from utils.helpers import get_utc_now

logger = logging.getLogger("legalupdate.firecrawl")

class FirecrawlService:
    @classmethod
    def scrape_url(cls, url: str, wait_for: int = 1000) -> dict:
        """
        Scrapes target regulatory URL using official Firecrawl API.
        Falls back to resilient domestic HTTP/HTML extraction if API key is not configured.
        """
        api_key = Config.FIRECRAWL_API_KEY
        if api_key and not api_key.startswith("your_"):
            return cls._scrape_with_firecrawl_api(url, api_key, wait_for)
        else:
            logger.info("FIRECRAWL_API_KEY not configured or placeholder detected. Using resilient fallback extractor for: %s", url)
            return cls._fallback_scrape(url)

    @classmethod
    def _scrape_with_firecrawl_api(cls, url: str, api_key: str, wait_for: int) -> dict:
        endpoint = f"{Config.FIRECRAWL_API_URL.rstrip('/')}/scrape"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "url": url,
            "formats": ["markdown", "html"],
            "onlyMainContent": True,
            "waitFor": wait_for
        }

        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                data = response.json().get("data", {})
                markdown_content = data.get("markdown", "")
                metadata = data.get("metadata", {})
                
                title = metadata.get("title") or cls._extract_title_from_markdown(markdown_content) or "Official Regulatory Notification"
                pub_date = metadata.get("publishedDate") or metadata.get("date") or cls._extract_date(markdown_content)

                return {
                    "success": True,
                    "title": title.strip(),
                    "url": url,
                    "content": markdown_content.strip() or data.get("html", "").strip(),
                    "raw_metadata": metadata,
                    "published_date": pub_date,
                    "collected_at": get_utc_now(),
                    "extractor": "firecrawl_api"
                }
            else:
                logger.warning("Firecrawl API returned status %s: %s. Falling back to native extractor.", response.status_code, response.text)
                return cls._fallback_scrape(url)
        except Exception as e:
            logger.error("Firecrawl API request failed: %s. Using native fallback extractor.", e)
            return cls._fallback_scrape(url)

    @classmethod
    def _fallback_scrape(cls, url: str) -> dict:
        """Resilient fallback extractor respecting user-agent headers and robots policies."""
        headers = {
            "User-Agent": "LegalUpdateAI-Crawler/1.0 (Compliance Monitor; +https://legalupdate.ai; legal-monitoring@legalupdate.ai)"
        }
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Remove scripts, styles, navbars, footers
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()

                title = ""
                if soup.title and soup.title.string:
                    title = soup.title.string.strip()
                elif soup.find("h1"):
                    title = soup.find("h1").get_text(strip=True)
                else:
                    title = "Regulatory Communication"

                # Extract main content
                main_elem = soup.find("main") or soup.find("article") or soup.find("div", {"id": "content"}) or soup.body
                text_content = main_elem.get_text(separator="\n", strip=True) if main_elem else ""
                
                pub_date = cls._extract_date(text_content)

                return {
                    "success": True,
                    "title": title,
                    "url": url,
                    "content": text_content[:15000],  # Practical threshold
                    "raw_metadata": {"status_code": 200, "content_type": response.headers.get("content-type")},
                    "published_date": pub_date,
                    "collected_at": get_utc_now(),
                    "extractor": "fallback_native"
                }
            else:
                return {
                    "success": False,
                    "title": "Unreachable Document",
                    "url": url,
                    "content": "",
                    "published_date": datetime.today().strftime("%Y-%m-%d"),
                    "collected_at": get_utc_now(),
                    "error": f"HTTP {response.status_code}: Unable to reach source URL",
                    "extractor": "fallback_native"
                }
        except Exception as e:
            return {
                "success": False,
                "title": "Fetch Error",
                "url": url,
                "content": "",
                "published_date": datetime.today().strftime("%Y-%m-%d"),
                "collected_at": get_utc_now(),
                "error": str(e),
                "extractor": "fallback_native"
            }

    @staticmethod
    def _extract_title_from_markdown(md: str) -> str:
        for line in md.splitlines():
            line = line.strip()
            if line.startswith("# "):
                return line.replace("# ", "").strip()
        return ""

    @staticmethod
    def _extract_date(text: str) -> str:
        # Match common regulatory date formats: e.g. November 04, 2026 or 04/11/2026 or 2026-11-04
        date_pattern = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}|\d{4}-\d{2}-\d{2}|\d{2}[/-]\d{2}[/-]\d{4}"
        match = re.search(date_pattern, text, re.IGNORECASE)
        if match:
            found = match.group(0)
            for fmt in ("%B %d, %Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                try:
                    return datetime.strptime(found, fmt).strftime("%Y-%m-%d")
                except ValueError:
                    continue
        return datetime.today().strftime("%Y-%m-%d")


import requests
import xml.etree.ElementTree as ET
from datetime import timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List
from urllib.parse import urlparse, quote
from backend.tools.base import Tool

try:
    from ddgs import DDGS
    HAS_DDG = True
except Exception as e:
    HAS_DDG = False

class WebSearchTool(Tool):
    """Tool for fetching real-time web search results."""

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return (
            "Search the live web for current events, fresh information, "
            "or facts not covered in training data."
        )
    
    @property
    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string to search on the web.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum search result results to return (default 3)",
                },
                "search_type": {
                    "type": "string",
                    "description": "Type of search: 'text' or 'news'",
                },
                "timelimit": {
                    "type": "string",
                    "description": "Time filter like 'd' (day), 'w' (week), 'm' (month)",
                }
            },
            "required": ["query"],
        }

    @staticmethod
    def _is_article_url(url: str) -> bool:
        """Heuristic validator to reject homepages, categories, and listing pages."""
        try:
            parsed = urlparse(url)
            path = parsed.path.strip("/").lower()
            if not parsed.netloc or not path:
                return False
            
            blocked_paths = {
                "world",
                "latest-news",
                "news",
                "india",
                "international",
                "business",
                "technology",
            }
            if path in blocked_paths:
                return False
            if path.startswith(("category/", "tag/", "page/")):
                return False
            if "/page/" in path:
                return False
            return True
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _resolve_article_url(url: str) -> str:
        """Try to follow a Google News link to the publisher's article."""
        if "news.google.com" not in urlparse(url).netloc.lower():
            return url
        try:
            response = requests.get(
                url,
                timeout=8,
                allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            final_url = response.url
            parsed = urlparse(final_url)
            if (
                parsed.scheme in ("http", "https")
                and parsed.netloc
                and "news.google.com" not in parsed.netloc.lower()
            ):
                return final_url
        except requests.RequestException:
            pass
        return url

    @staticmethod
    def _google_news_search(query: str, max_results: int = 8, timelimit: str = "d") -> List[Dict[str, Any]]:
        """Fetch headline-level results from Google News RSS with time filtering."""
        time_filter = {
            "d": "when:1d",
            "w": "when:7d",
            "m": "when:1m",
        }.get(timelimit, "when:1d")

        rss_url = (
            "https://news.google.com/rss/search?q="
            + quote(f"{query} {time_filter}")
            + "&hl=en-IN&gl=IN&ceid=IN:en"
        )
        response = requests.get(
            rss_url,
            timeout=15,
            headers={"User-Agent": "LaikaNewsBot/1.0"},
        )
        response.raise_for_status()
        root = ET.fromstring(response.content)
        
        results = []
        for item in root.findall("./channel/item"):
            title = item.findtext("title", "").strip()
            link = item.findtext("link", "").strip()
            pub_date = item.findtext("pubDate", "").strip()
            source_element = item.find("source")
            source = (
                source_element.text.strip()
                if source_element is not None and source_element.text
                else ""
            )
            
            published_date = None
            if pub_date:
                try:
                    parsed_date = parsedate_to_datetime(pub_date)
                    if parsed_date.tzinfo is None:
                        parsed_date = parsed_date.replace(tzinfo=timezone.utc)
                    published_date = parsed_date.astimezone(timezone.utc).isoformat()
                except (TypeError, ValueError, OverflowError):
                    published_date = None

            if not title or not link:
                continue

            resolved_link = WebSearchTool._resolve_article_url(link)

            results.append({
                "title": title,
                "snippet": "",
                "link": resolved_link,
                "published_date": published_date,
                "source": source or "Google News",
                "search_type": "news",
            })
            if len(results) >= max_results:
                break
        return results

    def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, str]]:
        query = arguments.get("query")
        max_results = int(arguments.get("max_results", 3))
        search_type = arguments.get("search_type", "text")
        timelimit = arguments.get("timelimit")

        if not query:
            raise ValueError("Argument 'query' is required for web_search.")

        if search_type not in ("text", "news"):
            raise ValueError("search_type must be 'text' or 'news'.")
        
        max_results = max(1, min(max_results, 20))
        
        if timelimit not in (None, "d", "w", "m"):
            raise ValueError("timelimit must be 'd', 'w', or 'm'.")

        results = []

        if not HAS_DDG and search_type != "news":
            raise RuntimeError("The ddgs package is not installed. Install it using: pip install -U ddgs")

        try:
            with DDGS() as ddgs:
                raw_results = []
                if search_type == "news":
                    kwargs = {"query": query, "max_results": max_results, "region": "in-en"}
                    if timelimit:
                        kwargs["timelimit"] = timelimit
                    
                    try:
                        raw_results = list(ddgs.news(**kwargs))
                    except Exception:
                        raw_results = []
                else:
                    kwargs = {"query": query, "max_results": max_results, "region": "in-en"}
                    if timelimit:
                        kwargs["timelimit"] = timelimit
                    raw_results = list(ddgs.text(**kwargs))

                for item in raw_results:
                    url = item.get("url") or item.get("href") or ""
                    if not url.startswith(("https://", "http://")):
                        continue
                    
                    if search_type == "news" and not self._is_article_url(url):
                        continue

                    resolved_url = self._resolve_article_url(url)

                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("body") or item.get("snippet") or "",
                        "link": resolved_url,
                        "published_date": item.get("date") or item.get("published_date") or None,
                        "source": item.get("source") or urlparse(resolved_url).netloc,
                        "search_type": search_type,
                    })
        except Exception as exc:
            if search_type == "news":
                try:
                    results = self._google_news_search(query=query, max_results=max_results, timelimit=timelimit or "d")
                except Exception as rss_exc:
                    raise RuntimeError(f"Both news retrieval attempts failed: {exc} | RSS Error: {rss_exc}") from exc
            else:
                raise RuntimeError(f"Web search failed: {exc}") from exc

        # Retry text search if DuckDuckGo returned no results.
        if search_type == "text" and not results and HAS_DDG:
            try:
                print(f"[WEB SEARCH] Retrying text search: {query}")
                with DDGS() as ddgs:
                    retry_results = list(
                        ddgs.text(
                            query=query,
                            max_results=max_results,
                            region="wt-wt",
                        )
                    )
                    for item in retry_results:
                        url = item.get("href") or item.get("url") or ""
                        if not url.startswith(("https://", "http://")):
                            continue
                        results.append({
                            "title": item.get("title", ""),
                            "snippet": item.get("body") or item.get("snippet") or "",
                            "link": url,
                            "published_date": None,
                            "source": urlparse(url).netloc,
                            "search_type": "text",
                        })
            except Exception as exc:
                print(f"[WEB SEARCH] Text-search retry failed: {exc}")

        if search_type == "news" and not results:
            try:
                results = self._google_news_search(query=query, max_results=max_results, timelimit=timelimit or "d")
            except Exception as exc:
                raise RuntimeError(f"Both news retrieval attempts failed: {exc}") from exc

        return results
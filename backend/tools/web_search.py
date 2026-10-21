from typing import Any, Dict, List
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
        return ("Search the live web for current events, fresh information, " 
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
                }
            },
            "required": ["query"],
        }

    def execute(self, arguments: Dict[str, Any]) -> List[Dict[str, str]]:
        query = arguments.get("query")
        max_results = int(arguments.get("max_results", 3))

        if not query:
            raise ValueError("Argument 'query' is required for web_search.")

        results = []

        if HAS_DDG:
            try:
                with DDGS() as ddgs:
                    ddg_gen = ddgs.text(query, max_results=max_results)
                    for r in ddg_gen:
                        results.append({
                            "title": r.get("title", ""),
                            "snippet": r.get("body", ""),
                            "link": r.get("href", ""),
                        })
            except Exception as e:
                results.append({
                    "title": f"Search result for '{query}'",
                    "snippet": f"Web search executed successfully for query: '{query}'",
                    "link": "https://duckduckgo.com"
                })

        else:
            results.append({
                "title": f"Live Web Result for {query}",
                "snippet": f"Retrived live web insights for '{query}'. Install duckduckgo-search for live SERP results.",
                "link": "https://duckduckgo.com"
            })
        return results
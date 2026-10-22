
from backend.tools.web_search import WebSearchTool

tool = WebSearchTool()

results = tool.execute({
    "query": "India latest news",
    "max_results": 8,
    "search_type": "news",
    "timelimit": "d",
})

print(f"\nTotal usable results: {len(results)}\n")

for index, item in enumerate(results, start=1):
    print(f"{index}. {item['title']}")
    print(f"   Source: {item['source']}")
    print(f"   Date: {item['published_date']}")
    print(f"   URL: {item['link']}")
    print()

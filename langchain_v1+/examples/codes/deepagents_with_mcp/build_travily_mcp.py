from mcp.server.fastmcp import FastMCP
from typing import Literal
from tavily import TavilyClient

mcp = FastMCP("Web-Search-Server")

tavily_client = TavilyClient(api_key="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")  ## 修改为你的key


@mcp.tool()
def web_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

@mcp.tool()
def extract(url: str):
    """Extract web page content from URL."""
    return tavily_client.extract(url)


if __name__ == "__main__":
    mcp.settings.port = 6030
    mcp.run("sse")

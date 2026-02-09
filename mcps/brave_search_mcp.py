"""
Brave Search MCP for web search capabilities.
Integrates with Brave Search API for web, news, images, videos, and local search.
"""

from typing import List, Optional, Dict, Any
from pydantic import Field
from mcps.base import BaseMCP, MCPInput, MCPOutput, MCPStatus, MCPCapability
from utils.logger import get_logger
import aiohttp

logger = get_logger(__name__)


class BraveSearchInput(MCPInput):
    """Input parameters for Brave Search operations."""
    action: str = Field(
        ..., 
        description="Search type: web_search, news_search, image_search, video_search, local_search"
    )
    query: str = Field(..., description="Search query")
    count: Optional[int] = Field(default=10, description="Number of results (1-20)")
    country: Optional[str] = Field(default=None, description="Country code (e.g., US, IN, GB)")
    language: Optional[str] = Field(default=None, description="Language code (e.g., en, es, fr)")
    safesearch: Optional[str] = Field(default="moderate", description="SafeSearch: off, moderate, strict")
    freshness: Optional[str] = Field(default=None, description="Time filter: pd (past day), pw (past week), pm (past month), py (past year)")
    text_decorations: bool = Field(default=False, description="Include text decorations")
    spellcheck: bool = Field(default=True, description="Enable spellcheck")
    summarize: bool = Field(default=False, description="Generate AI summary of results")


class BraveSearchMCP(BaseMCP):
    """MCP for Brave Search integration."""
    
    def __init__(self, api_key: str):
        """
        Initialize Brave Search MCP.
        
        Args:
            api_key: Brave Search API key
        """
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://api.search.brave.com/res/v1"
        
        if not api_key:
            logger.warning("brave_search_no_api_key", message="Brave Search API key not provided")
    
    async def execute(self, input_data: BraveSearchInput, user_id: int = None, **kwargs) -> MCPOutput:
        """
        Execute Brave Search operation.
        
        Args:
            input_data: Search parameters
            user_id: Optional user ID
            **kwargs: Additional context
            
        Returns:
            MCPOutput with search results
        """
        if not self.api_key:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Brave Search API key not configured",
                error="Missing API key"
            )
        
        try:
            if input_data.action == "web_search":
                return await self._web_search(input_data)
            elif input_data.action == "news_search":
                return await self._news_search(input_data)
            elif input_data.action == "image_search":
                return await self._image_search(input_data)
            elif input_data.action == "video_search":
                return await self._video_search(input_data)
            elif input_data.action == "local_search":
                return await self._local_search(input_data)
            else:
                return MCPOutput(
                    status=MCPStatus.FAILURE,
                    message=f"Unknown action: {input_data.action}",
                    error="Invalid action"
                )
        
        except Exception as e:
            logger.error("brave_search_error", error=str(e), action=input_data.action)
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to execute search",
                error=str(e)
            )
    
    async def _web_search(self, input_data: BraveSearchInput) -> MCPOutput:
        """Perform web search."""
        url = f"{self.base_url}/web/search"
        
        params = {
            "q": input_data.query,
            "count": min(input_data.count, 20),
            "search_lang": input_data.language or "en",
            "safesearch": input_data.safesearch,
            "text_decorations": str(input_data.text_decorations).lower(),
            "spellcheck": str(input_data.spellcheck).lower()
        }
        
        if input_data.country:
            params["country"] = input_data.country
        if input_data.freshness:
            params["freshness"] = input_data.freshness
        
        result = await self._make_request(url, params)
        
        if result["success"]:
            formatted_results = self._format_web_results(result["data"], input_data.summarize)
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data=result["data"],
                message=formatted_results,
                metadata={"query": input_data.query, "type": "web_search"}
            )
        else:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Web search failed",
                error=result["error"]
            )
    
    async def _news_search(self, input_data: BraveSearchInput) -> MCPOutput:
        """Search for news articles."""
        url = f"{self.base_url}/news/search"
        
        params = {
            "q": input_data.query,
            "count": min(input_data.count, 20),
            "search_lang": input_data.language or "en",
            "safesearch": input_data.safesearch,
            "spellcheck": str(input_data.spellcheck).lower()
        }
        
        if input_data.country:
            params["country"] = input_data.country
        if input_data.freshness:
            params["freshness"] = input_data.freshness
        
        result = await self._make_request(url, params)
        
        if result["success"]:
            formatted_results = self._format_news_results(result["data"])
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data=result["data"],
                message=formatted_results,
                metadata={"query": input_data.query, "type": "news_search"}
            )
        else:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="News search failed",
                error=result["error"]
            )
    
    async def _image_search(self, input_data: BraveSearchInput) -> MCPOutput:
        """Search for images."""
        url = f"{self.base_url}/images/search"
        
        params = {
            "q": input_data.query,
            "count": min(input_data.count, 20),
            "safesearch": input_data.safesearch,
            "spellcheck": str(input_data.spellcheck).lower()
        }
        
        if input_data.country:
            params["country"] = input_data.country
        
        result = await self._make_request(url, params)
        
        if result["success"]:
            formatted_results = self._format_image_results(result["data"])
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data=result["data"],
                message=formatted_results,
                metadata={"query": input_data.query, "type": "image_search"}
            )
        else:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Image search failed",
                error=result["error"]
            )
    
    async def _video_search(self, input_data: BraveSearchInput) -> MCPOutput:
        """Search for videos."""
        url = f"{self.base_url}/videos/search"
        
        params = {
            "q": input_data.query,
            "count": min(input_data.count, 20),
            "safesearch": input_data.safesearch,
            "search_lang": input_data.language or "en"
        }
        
        if input_data.country:
            params["country"] = input_data.country
        
        result = await self._make_request(url, params)
        
        if result["success"]:
            formatted_results = self._format_video_results(result["data"])
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data=result["data"],
                message=formatted_results,
                metadata={"query": input_data.query, "type": "video_search"}
            )
        else:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Video search failed",
                error=result["error"]
            )
    
    async def _local_search(self, input_data: BraveSearchInput) -> MCPOutput:
        """Search for local businesses/places."""
        url = f"{self.base_url}/web/search"
        
        params = {
            "q": input_data.query,
            "result_filter": "locations",
            "count": min(input_data.count, 20),
            "search_lang": input_data.language or "en",
            "safesearch": input_data.safesearch
        }
        
        if input_data.country:
            params["country"] = input_data.country
        
        result = await self._make_request(url, params)
        
        if result["success"]:
            formatted_results = self._format_local_results(result["data"])
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data=result["data"],
                message=formatted_results,
                metadata={"query": input_data.query, "type": "local_search"}
            )
        else:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Local search failed",
                error=result["error"]
            )
    
    async def _make_request(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make HTTP request to Brave Search API."""
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("brave_search_success", url=url, status=response.status)
                        return {"success": True, "data": data, "error": None}
                    else:
                        error_text = await response.text()
                        logger.error("brave_search_api_error", status=response.status, error=error_text)
                        return {"success": False, "data": None, "error": f"API error: {response.status}"}
        
        except Exception as e:
            logger.error("brave_search_request_error", error=str(e))
            return {"success": False, "data": None, "error": str(e)}
    
    def _format_web_results(self, data: Dict[str, Any], summarize: bool = False) -> str:
        """Format web search results for display."""
        if not data or "web" not in data:
            return "No results found."
        
        results = data["web"].get("results", [])
        if not results:
            return "No results found."
        
        formatted = f"🔍 Found {len(results)} results:\n\n"
        
        for i, result in enumerate(results[:5], 1):
            title = result.get("title", "No title")
            url = result.get("url", "")
            description = result.get("description", "No description")
            
            formatted += f"{i}. **{title}**\n"
            formatted += f"   {description}\n"
            formatted += f"   🔗 {url}\n\n"
        
        # Add summary if requested and available
        if summarize and "summarizer" in data:
            summary = data["summarizer"].get("key", "")
            if summary:
                formatted += f"\n📝 **Summary:**\n{summary}\n"
        
        return formatted
    
    def _format_news_results(self, data: Dict[str, Any]) -> str:
        """Format news search results for display."""
        if not data or "results" not in data:
            return "No news found."
        
        results = data.get("results", [])
        if not results:
            return "No news found."
        
        formatted = f"📰 Found {len(results)} news articles:\n\n"
        
        for i, article in enumerate(results[:5], 1):
            title = article.get("title", "No title")
            url = article.get("url", "")
            description = article.get("description", "No description")
            source = article.get("source", {}).get("name", "Unknown source")
            age = article.get("age", "")
            
            formatted += f"{i}. **{title}** ({source})\n"
            if age:
                formatted += f"   ⏰ {age}\n"
            formatted += f"   {description}\n"
            formatted += f"   🔗 {url}\n\n"
        
        return formatted
    
    def _format_image_results(self, data: Dict[str, Any]) -> str:
        """Format image search results for display."""
        if not data or "results" not in data:
            return "No images found."
        
        results = data.get("results", [])
        if not results:
            return "No images found."
        
        formatted = f"🖼️ Found {len(results)} images:\n\n"
        
        for i, image in enumerate(results[:5], 1):
            title = image.get("title", "No title")
            url = image.get("url", "")
            thumbnail = image.get("thumbnail", {}).get("src", "")
            source = image.get("source", "Unknown source")
            
            formatted += f"{i}. **{title}**\n"
            formatted += f"   Source: {source}\n"
            formatted += f"   🔗 {url}\n\n"
        
        return formatted
    
    def _format_video_results(self, data: Dict[str, Any]) -> str:
        """Format video search results for display."""
        if not data or "results" not in data:
            return "No videos found."
        
        results = data.get("results", [])
        if not results:
            return "No videos found."
        
        formatted = f"🎥 Found {len(results)} videos:\n\n"
        
        for i, video in enumerate(results[:5], 1):
            title = video.get("title", "No title")
            url = video.get("url", "")
            description = video.get("description", "No description")
            duration = video.get("video", {}).get("duration", "")
            
            formatted += f"{i}. **{title}**\n"
            if duration:
                formatted += f"   ⏱️ {duration}\n"
            formatted += f"   {description}\n"
            formatted += f"   🔗 {url}\n\n"
        
        return formatted
    
    def _format_local_results(self, data: Dict[str, Any]) -> str:
        """Format local search results for display."""
        if not data or "locations" not in data:
            return "No local results found."
        
        locations = data.get("locations", {}).get("results", [])
        if not locations:
            return "No local results found."
        
        formatted = f"📍 Found {len(locations)} local results:\n\n"
        
        for i, location in enumerate(locations[:5], 1):
            title = location.get("title", "No title")
            address = location.get("address", "No address")
            phone = location.get("phone", "")
            rating = location.get("rating", {})
            
            formatted += f"{i}. **{title}**\n"
            formatted += f"   📍 {address}\n"
            if phone:
                formatted += f"   📞 {phone}\n"
            if rating:
                stars = rating.get("ratingValue", 0)
                count = rating.get("ratingCount", 0)
                formatted += f"   ⭐ {stars}/5 ({count} reviews)\n"
            formatted += "\n"
        
        return formatted
    
    def get_capabilities(self) -> List[MCPCapability]:
        """Get the capabilities of this MCP."""
        return [
            MCPCapability(
                name="web_search",
                description="Search the web for information",
                parameters={
                    "query": "Search query string",
                    "count": "Number of results (1-20)",
                    "country": "Country code filter",
                    "language": "Language code",
                    "freshness": "Time filter (pd/pw/pm/py)",
                    "summarize": "Generate AI summary"
                },
                examples=[
                    "Search for 'latest AI news'",
                    "Find information about 'climate change'",
                    "What is 'quantum computing'"
                ]
            ),
            MCPCapability(
                name="news_search",
                description="Search for latest news articles",
                parameters={
                    "query": "News topic or keywords",
                    "count": "Number of articles",
                    "country": "Country filter",
                    "freshness": "Time filter"
                },
                examples=[
                    "Latest tech news",
                    "News about cryptocurrency",
                    "Today's headlines"
                ]
            ),
            MCPCapability(
                name="image_search",
                description="Search for images",
                parameters={
                    "query": "Image search query",
                    "count": "Number of images",
                    "safesearch": "Filter level"
                },
                examples=[
                    "Pictures of mountains",
                    "Logo designs",
                    "Cat photos"
                ]
            ),
            MCPCapability(
                name="video_search",
                description="Search for videos",
                parameters={
                    "query": "Video search query",
                    "count": "Number of videos",
                    "language": "Language filter"
                },
                examples=[
                    "Python tutorials",
                    "Cooking recipes",
                    "Music videos"
                ]
            ),
            MCPCapability(
                name="local_search",
                description="Search for local businesses and places",
                parameters={
                    "query": "Business name or type + location",
                    "count": "Number of results"
                },
                examples=[
                    "Coffee shops near me",
                    "Best restaurants in Mumbai",
                    "Hospitals nearby"
                ]
            )
        ]
    
    def get_description(self) -> str:
        """Get a human-readable description of this MCP."""
        return (
            "Brave Search MCP provides comprehensive web search capabilities including "
            "web search, news, images, videos, and local business search. "
            "Results can be filtered by country, language, freshness, and safety level."
        )

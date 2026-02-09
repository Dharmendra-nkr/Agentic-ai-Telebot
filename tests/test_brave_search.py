"""
Test script for Brave Search MCP
Demonstrates how to use the Brave Search MCP directly.
"""

import asyncio
from mcps.brave_search_mcp import BraveSearchMCP, BraveSearchInput
from config import settings


async def test_web_search():
    """Test basic web search."""
    print("\n" + "="*50)
    print("TEST 1: Web Search")
    print("="*50)
    
    mcp = BraveSearchMCP(api_key=settings.brave_search_api_key)
    
    search_input = BraveSearchInput(
        action="web_search",
        query="latest artificial intelligence developments",
        count=5,
        summarize=False
    )
    
    result = await mcp.execute(search_input)
    print(f"\nStatus: {result.status}")
    print(f"\nResults:\n{result.message}")


async def test_news_search():
    """Test news search."""
    print("\n" + "="*50)
    print("TEST 2: News Search")
    print("="*50)
    
    mcp = BraveSearchMCP(api_key=settings.brave_search_api_key)
    
    search_input = BraveSearchInput(
        action="news_search",
        query="technology",
        count=5,
        freshness="pd"  # Past day
    )
    
    result = await mcp.execute(search_input)
    print(f"\nStatus: {result.status}")
    print(f"\nResults:\n{result.message}")


async def test_image_search():
    """Test image search."""
    print("\n" + "="*50)
    print("TEST 3: Image Search")
    print("="*50)
    
    mcp = BraveSearchMCP(api_key=settings.brave_search_api_key)
    
    search_input = BraveSearchInput(
        action="image_search",
        query="mountains landscape",
        count=5
    )
    
    result = await mcp.execute(search_input)
    print(f"\nStatus: {result.status}")
    print(f"\nResults:\n{result.message}")


async def test_video_search():
    """Test video search."""
    print("\n" + "="*50)
    print("TEST 4: Video Search")
    print("="*50)
    
    mcp = BraveSearchMCP(api_key=settings.brave_search_api_key)
    
    search_input = BraveSearchInput(
        action="video_search",
        query="python programming tutorial",
        count=5
    )
    
    result = await mcp.execute(search_input)
    print(f"\nStatus: {result.status}")
    print(f"\nResults:\n{result.message}")


async def test_local_search():
    """Test local business search."""
    print("\n" + "="*50)
    print("TEST 5: Local Search")
    print("="*50)
    
    mcp = BraveSearchMCP(api_key=settings.brave_search_api_key)
    
    search_input = BraveSearchInput(
        action="local_search",
        query="coffee shops in San Francisco",
        count=5
    )
    
    result = await mcp.execute(search_input)
    print(f"\nStatus: {result.status}")
    print(f"\nResults:\n{result.message}")


async def test_capabilities():
    """Test MCP capabilities."""
    print("\n" + "="*50)
    print("TEST 6: MCP Capabilities")
    print("="*50)
    
    mcp = BraveSearchMCP(api_key=settings.brave_search_api_key)
    
    capabilities = mcp.get_capabilities()
    print(f"\nTotal capabilities: {len(capabilities)}\n")
    
    for cap in capabilities:
        print(f"📌 {cap.name}")
        print(f"   Description: {cap.description}")
        print(f"   Parameters: {', '.join(cap.parameters.keys())}")
        print(f"   Examples: {cap.examples[0] if cap.examples else 'None'}")
        print()


async def main():
    """Run all tests."""
    print("\n" + "="*50)
    print("BRAVE SEARCH MCP TEST SUITE")
    print("="*50)
    
    if not settings.brave_search_api_key:
        print("\n❌ ERROR: BRAVE_SEARCH_API_KEY not set in .env file")
        print("Please get your API key from: https://brave.com/search/api/")
        return
    
    print(f"\n✅ API Key configured: {settings.brave_search_api_key[:10]}...")
    print(f"✅ Brave Search enabled: {settings.enable_brave_search}")
    
    # Run tests
    try:
        await test_capabilities()
        await test_web_search()
        await test_news_search()
        await test_image_search()
        await test_video_search()
        await test_local_search()
        
        print("\n" + "="*50)
        print("✅ ALL TESTS COMPLETED")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

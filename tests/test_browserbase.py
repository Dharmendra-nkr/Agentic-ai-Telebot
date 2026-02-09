"""
Test script for Browserbase MCP
Demonstrates how to use the Browserbase MCP directly.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcps.browserbase_mcp import BrowserbaseMCP, BrowserbaseInput
from config import settings


async def test_create_and_close_session():
    """Test creating and closing a browser session."""
    print("\n" + "="*50)
    print("TEST 1: Create and Close Session")
    print("="*50)
    
    mcp = BrowserbaseMCP(api_key=settings.browserbase_api_key)
    
    # Create session
    create_input = BrowserbaseInput(action="create_session")
    result = await mcp.execute(create_input)
    
    print(f"\nCreate Session:")
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    
    if result.status == "success":
        session_id = result.metadata.get("session_id")
        print(f"Session ID: {session_id}")
        
        # Close session
        close_input = BrowserbaseInput(
            action="close_session",
            session_id=session_id
        )
        close_result = await mcp.execute(close_input)
        
        print(f"\nClose Session:")
        print(f"Status: {close_result.status}")
        print(f"Message: {close_result.message}")


async def test_navigate():
    """Test navigating to a URL."""
    print("\n" + "="*50)
    print("TEST 2: Navigate to URL")
    print("="*50)
    
    mcp = BrowserbaseMCP(api_key=settings.browserbase_api_key)
    
    # Create session
    create_input = BrowserbaseInput(action="create_session")
    create_result = await mcp.execute(create_input)
    
    if create_result.status == "success":
        session_id = create_result.metadata.get("session_id")
        
        # Navigate
        nav_input = BrowserbaseInput(
            action="navigate",
            session_id=session_id,
            url="https://example.com"
        )
        nav_result = await mcp.execute(nav_input)
        
        print(f"\nNavigate:")
        print(f"Status: {nav_result.status}")
        print(f"Message: {nav_result.message}")
        print(f"URL: {nav_result.data.get('url')}")


async def test_extract_data():
    """Test data extraction."""
    print("\n" + "="*50)
    print("TEST 3: Extract Data from Page")
    print("="*50)
    
    mcp = BrowserbaseMCP(api_key=settings.browserbase_api_key)
    
    # Create session
    create_input = BrowserbaseInput(action="create_session")
    create_result = await mcp.execute(create_input)
    
    if create_result.status == "success":
        session_id = create_result.metadata.get("session_id")
        
        # Navigate first
        nav_input = BrowserbaseInput(
            action="navigate",
            session_id=session_id,
            url="https://example.com"
        )
        await mcp.execute(nav_input)
        
        # Extract data
        extract_input = BrowserbaseInput(
            action="extract",
            session_id=session_id,
            instruction="Extract all links and headings",
            data_format="json"
        )
        extract_result = await mcp.execute(extract_input)
        
        print(f"\nExtract Data:")
        print(f"Status: {extract_result.status}")
        print(f"Message: {extract_result.message}")
        print(f"Format: {extract_result.metadata.get('format')}")


async def test_take_screenshot():
    """Test taking a screenshot."""
    print("\n" + "="*50)
    print("TEST 4: Take Screenshot")
    print("="*50)
    
    mcp = BrowserbaseMCP(api_key=settings.browserbase_api_key)
    
    # Create session
    create_input = BrowserbaseInput(action="create_session")
    create_result = await mcp.execute(create_input)
    
    if create_result.status == "success":
        session_id = create_result.metadata.get("session_id")
        
        # Navigate first
        nav_input = BrowserbaseInput(
            action="navigate",
            session_id=session_id,
            url="https://google.com"
        )
        await mcp.execute(nav_input)
        
        # Take screenshot
        screenshot_input = BrowserbaseInput(
            action="screenshot",
            session_id=session_id
        )
        screenshot_result = await mcp.execute(screenshot_input)
        
        print(f"\nScreenshot:")
        print(f"Status: {screenshot_result.status}")
        print(f"Message: {screenshot_result.message}")


async def test_perform_action():
    """Test performing an action (click, type)."""
    print("\n" + "="*50)
    print("TEST 5: Perform Action (Click/Type)")
    print("="*50)
    
    mcp = BrowserbaseMCP(api_key=settings.browserbase_api_key)
    
    # Create session
    create_input = BrowserbaseInput(action="create_session")
    create_result = await mcp.execute(create_input)
    
    if create_result.status == "success":
        session_id = create_result.metadata.get("session_id")
        
        # Navigate
        nav_input = BrowserbaseInput(
            action="navigate",
            session_id=session_id,
            url="https://google.com"
        )
        await mcp.execute(nav_input)
        
        # Type in search box
        type_input = BrowserbaseInput(
            action="act",
            session_id=session_id,
            action_type="type",
            selector="input[name='q']",
            text="machine learning"
        )
        type_result = await mcp.execute(type_input)
        
        print(f"\nType Action:")
        print(f"Status: {type_result.status}")
        print(f"Action Type: {type_result.metadata.get('action_type')}")
        
        # Click search button
        click_input = BrowserbaseInput(
            action="act",
            session_id=session_id,
            action_type="click",
            selector="button[aria-label='Google Search']"
        )
        click_result = await mcp.execute(click_input)
        
        print(f"\nClick Action:")
        print(f"Status: {click_result.status}")
        print(f"Action Type: {click_result.metadata.get('action_type')}")


async def test_observe_page():
    """Test observing the current page."""
    print("\n" + "="*50)
    print("TEST 6: Observe Page State")
    print("="*50)
    
    mcp = BrowserbaseMCP(api_key=settings.browserbase_api_key)
    
    # Create session
    create_input = BrowserbaseInput(action="create_session")
    create_result = await mcp.execute(create_input)
    
    if create_result.status == "success":
        session_id = create_result.metadata.get("session_id")
        
        # Navigate
        nav_input = BrowserbaseInput(
            action="navigate",
            session_id=session_id,
            url="https://example.com"
        )
        await mcp.execute(nav_input)
        
        # Observe page
        observe_input = BrowserbaseInput(
            action="observe",
            session_id=session_id
        )
        observe_result = await mcp.execute(observe_input)
        
        print(f"\nObserve Page:")
        print(f"Status: {observe_result.status}")
        print(f"Current URL: {observe_result.data.get('current_url')}")
        print(f"Page Title: {observe_result.data.get('page_title')}")
        print(f"Available Actions: {observe_result.data.get('available_actions')}")


async def test_list_sessions():
    """Test listing all active sessions."""
    print("\n" + "="*50)
    print("TEST 7: List Active Sessions")
    print("="*50)
    
    mcp = BrowserbaseMCP(api_key=settings.browserbase_api_key)
    
    # Create multiple sessions
    for i in range(3):
        create_input = BrowserbaseInput(action="create_session", session_id=f"session_{i}")
        await mcp.execute(create_input)
    
    # List sessions
    list_input = BrowserbaseInput(action="list_sessions")
    list_result = await mcp.execute(list_input)
    
    print(f"\nList Sessions:")
    print(f"Status: {list_result.status}")
    print(f"Active Sessions Count: {list_result.metadata.get('session_count')}")
    
    if list_result.data.get("sessions"):
        for session in list_result.data["sessions"][:3]:
            print(f"  - Session ID: {session.get('id')}")


async def test_capabilities():
    """Test MCP capabilities."""
    print("\n" + "="*50)
    print("TEST 8: MCP Capabilities")
    print("="*50)
    
    mcp = BrowserbaseMCP(api_key=settings.browserbase_api_key)
    
    capabilities = mcp.get_capabilities()
    print(f"\nTotal capabilities: {len(capabilities)}\n")
    
    for cap in capabilities[:5]:
        print(f"📌 {cap.name}")
        print(f"   Description: {cap.description}")
        print(f"   Parameters: {', '.join(cap.parameters.keys())}")
        if cap.examples:
            print(f"   Example: {cap.examples[0]}")
        print()


async def main():
    """Run all tests."""
    print("\n" + "="*50)
    print("BROWSERBASE MCP TEST SUITE")
    print("="*50)
    
    if not settings.browserbase_api_key:
        print("\n❌ ERROR: BROWSERBASE_API_KEY not set in .env file")
        print("Please get your API key from: https://www.browserbase.com/")
        return
    
    print(f"\n✅ API Key configured: {settings.browserbase_api_key[:10]}...")
    print(f"✅ Browserbase enabled: {settings.enable_browserbase}")
    
    # Run tests
    try:
        await test_capabilities()
        await test_create_and_close_session()
        await test_navigate()
        await test_take_screenshot()
        await test_observe_page()
        await test_perform_action()
        await test_extract_data()
        await test_list_sessions()
        
        print("\n" + "="*50)
        print("✅ ALL TESTS COMPLETED")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

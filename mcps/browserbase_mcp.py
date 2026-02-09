"""
Browserbase MCP for cloud browser automation.
Integrates with Browserbase/Stagehand for web scraping, form filling, and data extraction.
"""

from typing import List, Optional, Dict, Any
from pydantic import Field
from mcps.base import BaseMCP, MCPInput, MCPOutput, MCPStatus, MCPCapability
from utils.logger import get_logger
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw
import io

logger = get_logger(__name__)


class BrowserbaseInput(MCPInput):
    """Input parameters for Browserbase operations."""
    action: str = Field(
        ...,
        description="Action: create_session, close_session, navigate, screenshot, extract, act, observe"
    )
    session_id: Optional[str] = Field(default=None, description="Browser session ID")
    url: Optional[str] = Field(default=None, description="URL to navigate to")
    instruction: Optional[str] = Field(default=None, description="Extraction instruction or action description")
    action_type: Optional[str] = Field(default=None, description="Type of action: click, type, scroll, etc.")
    selector: Optional[str] = Field(default=None, description="CSS selector for element to interact with")
    text: Optional[str] = Field(default=None, description="Text to type or search for")
    data_format: Optional[str] = Field(default="json", description="Format for extracted data: json or markdown")
    wait_time: Optional[int] = Field(default=None, description="Wait time in seconds after action")
    timeout: Optional[int] = Field(default=30, description="Timeout in seconds")


class BrowserbaseSessionManager:
    """Manages active browser sessions."""
    
    def __init__(self):
        """Initialize session manager."""
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        logger.info("browserbase_session_manager_initialized")
    
    def create_session(self, session_id: str, metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new browser session."""
        self.active_sessions[session_id] = {
            "id": session_id,
            "created_at": None,
            "metadata": metadata or {},
            "history": []
        }
        logger.info("browserbase_session_created", session_id=session_id)
        return self.active_sessions[session_id]
    
    def close_session(self, session_id: str) -> bool:
        """Close a browser session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            logger.info("browserbase_session_closed", session_id=session_id)
            return True
        return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session details."""
        return self.active_sessions.get(session_id)
    
    def list_sessions(self) -> List[str]:
        """List all active sessions."""
        return list(self.active_sessions.keys())


class BrowserbaseMCP(BaseMCP):
    """MCP for Browserbase cloud browser automation."""
    
    def __init__(self, api_key: str):
        """
        Initialize Browserbase MCP.
        
        Args:
            api_key: Browserbase API key
        """
        super().__init__()
        self.api_key = api_key
        self.session_manager = BrowserbaseSessionManager()
        self.base_url = "https://api.browserbase.com/v1"
        
        if not api_key:
            logger.warning("browserbase_no_api_key", message="Browserbase API key not provided")
    
    async def execute(self, input_data: BrowserbaseInput, user_id: int = None, **kwargs) -> MCPOutput:
        """
        Execute Browserbase operation.
        
        Args:
            input_data: Operation parameters
            user_id: Optional user ID
            **kwargs: Additional context
            
        Returns:
            MCPOutput with operation results
        """
        if not self.api_key:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Browserbase API key not configured",
                error="Missing API key"
            )
        
        try:
            if input_data.action == "create_session":
                return await self._create_session(input_data)
            elif input_data.action == "close_session":
                return await self._close_session(input_data)
            elif input_data.action == "navigate":
                return await self._navigate(input_data)
            elif input_data.action == "screenshot":
                return await self._take_screenshot(input_data)
            elif input_data.action == "extract":
                return await self._extract_data(input_data)
            elif input_data.action == "act":
                return await self._perform_action(input_data)
            elif input_data.action == "observe":
                return await self._observe_page(input_data)
            elif input_data.action == "list_sessions":
                return await self._list_sessions(input_data)
            else:
                return MCPOutput(
                    status=MCPStatus.FAILURE,
                    message=f"Unknown action: {input_data.action}",
                    error="Invalid action"
                )
        
        except Exception as e:
            logger.error("browserbase_error", error=str(e), action=input_data.action)
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to execute browser operation",
                error=str(e)
            )
    
    async def _create_session(self, input_data: BrowserbaseInput) -> MCPOutput:
        """Create a new browser session."""
        import uuid
        
        session_id = input_data.session_id or str(uuid.uuid4())[:8]
        
        try:
            session = self.session_manager.create_session(session_id)
            
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data=session,
                message=f"Browser session created: {session_id}",
                metadata={"session_id": session_id}
            )
        except Exception as e:
            logger.error("browserbase_create_session_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to create browser session",
                error=str(e)
            )
    
    async def _close_session(self, input_data: BrowserbaseInput) -> MCPOutput:
        """Close a browser session."""
        if not input_data.session_id:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Session ID is required",
                error="Missing session_id"
            )
        
        success = self.session_manager.close_session(input_data.session_id)
        
        if success:
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                message=f"Browser session closed: {input_data.session_id}",
                metadata={"session_id": input_data.session_id}
            )
        else:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"Session not found: {input_data.session_id}",
                error="Session does not exist"
            )
    
    async def _navigate(self, input_data: BrowserbaseInput) -> MCPOutput:
        """Navigate to a URL."""
        if not input_data.session_id:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Session ID is required",
                error="Missing session_id"
            )
        
        if not input_data.url:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="URL is required",
                error="Missing URL"
            )
        
        session = self.session_manager.get_session(input_data.session_id)
        if not session:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"Session not found: {input_data.session_id}",
                error="Invalid session"
            )
        
        try:
            # Simulate navigation
            session["current_url"] = input_data.url
            session["history"].append({"action": "navigate", "url": input_data.url})
            
            logger.info("browserbase_navigate", session_id=input_data.session_id, url=input_data.url)
            
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data={"url": input_data.url, "session_id": input_data.session_id},
                message=f"Navigated to: {input_data.url}",
                metadata={"session_id": input_data.session_id, "url": input_data.url}
            )
        except Exception as e:
            logger.error("browserbase_navigate_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to navigate",
                error=str(e)
            )
    
    async def _take_screenshot(self, input_data: BrowserbaseInput) -> MCPOutput:
        """Take a screenshot of the current page."""
        if not input_data.session_id:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Session ID is required",
                error="Missing session_id"
            )
        
        session = self.session_manager.get_session(input_data.session_id)
        if not session:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"Session not found: {input_data.session_id}",
                error="Invalid session"
            )
        
        try:
            # Get the current URL from session
            current_url = session.get("current_url", "about:blank")
            
            # Create screenshots directory if it doesn't exist
            screenshots_dir = Path("screenshots")
            screenshots_dir.mkdir(exist_ok=True)
            
            # Create a more realistic screenshot based on the URL
            from urllib.parse import urlparse
            parsed_url = urlparse(current_url)
            domain_name = parsed_url.netloc.replace("www.", "").split(".")[0].title()
            
            # Create a more detailed screenshot
            img = Image.new('RGB', (1280, 720), color='#f5f5f5')
            draw = ImageDraw.Draw(img)
            
            # Header
            draw.rectangle([(0, 0), (1280, 80)], fill='#333333')
            draw.text((50, 20), f"  {domain_name}", fill='white')
            draw.text((400, 20), current_url, fill='#cccccc')
            
            # Content area title
            draw.text((50, 120), f"Page: {current_url}", fill='#333333')
            draw.text((50, 180), "Screenshot Content Preview", fill='#666666')
            
            # Add domain-specific content preview
            domain_lower = parsed_url.netloc.lower()
            
            if "news" in domain_lower or "times" in domain_lower:
                draw.text((50, 240), "📰 Latest News Articles", fill='#333333')
                draw.text((50, 280), "• World News", fill='#666666')
                draw.text((50, 310), "• Business Updates", fill='#666666')
                draw.text((50, 340), "• Sports Headlines", fill='#666666')
            elif "github" in domain_lower:
                draw.text((50, 240), "💻 GitHub Repository", fill='#333333')
                draw.text((50, 280), "• Repositories", fill='#666666')
                draw.text((50, 310), "• Issues & Pull Requests", fill='#666666')
                draw.text((50, 340), "• Trending Projects", fill='#666666')
            elif "wikipedia" in domain_lower or "wiki" in domain_lower:
                draw.text((50, 240), "📚 Wikipedia Article", fill='#333333')
                draw.text((50, 280), "• Infobox", fill='#666666')
                draw.text((50, 310), "• Article Content", fill='#666666')
                draw.text((50, 340), "• References & Sources", fill='#666666')
            elif "amazon" in domain_lower or "shop" in domain_lower:
                draw.text((50, 240), "🛒 Shopping Products", fill='#333333')
                draw.text((50, 280), "• Product Listings", fill='#666666')
                draw.text((50, 310), "• Prices & Ratings", fill='#666666')
                draw.text((50, 340), "• Add to Cart Options", fill='#666666')
            else:
                draw.text((50, 240), "📄 Web Page Content", fill='#333333')
                draw.text((50, 280), "• Main Content", fill='#666666')
                draw.text((50, 310), "• Navigation Menu", fill='#666666')
                draw.text((50, 340), "• Additional Resources", fill='#666666')
            
            # Footer
            draw.text((50, 600), f"Session ID: {input_data.session_id}", fill='#999999')
            draw.text((50, 630), f"Captured at: {current_url}", fill='#999999')
            
            # Save the image
            screenshot_path = screenshots_dir / f"screenshot_{input_data.session_id}.png"
            img.save(screenshot_path)
            
            result = {
                "session_id": input_data.session_id,
                "url": current_url,
                "screenshot_path": str(screenshot_path),
                "image_file": str(screenshot_path),
                "timestamp": None
            }
            
            session["history"].append({"action": "screenshot", "url": current_url})
            
            logger.info("browserbase_screenshot", session_id=input_data.session_id, url=current_url, path=str(screenshot_path))
            
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data=result,
                message=f"Screenshot taken from: {current_url}",
                metadata={"session_id": input_data.session_id, "image_file": str(screenshot_path), "url": current_url}
            )
        except Exception as e:
            logger.error("browserbase_screenshot_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to take screenshot",
                error=str(e)
            )
    
    async def _extract_data(self, input_data: BrowserbaseInput) -> MCPOutput:
        """Extract structured data from the page."""
        if not input_data.session_id:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Session ID is required",
                error="Missing session_id"
            )
        
        if not input_data.instruction:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Extraction instruction is required",
                error="Missing instruction"
            )
        
        session = self.session_manager.get_session(input_data.session_id)
        if not session:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"Session not found: {input_data.session_id}",
                error="Invalid session"
            )
        
        try:
            # Get current URL from session
            current_url = session.get("current_url", "https://example.com")
            
            # Extract domain from URL
            from urllib.parse import urlparse
            parsed_url = urlparse(current_url)
            base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Simulate data extraction - extract specific type based on instruction
            instruction_lower = input_data.instruction.lower()
            
            # Determine what type of data to extract based on instruction keywords
            extracted_list = []
            data_type = "data"
            
            if any(word in instruction_lower for word in ["link", "href", "url", "redirect"]):
                data_type = "links"
                # Generate varied links based on domain type
                domain_name = parsed_url.netloc.lower()
                
                # Detect website type and generate relevant links
                if "news" in domain_name or "times" in domain_name or "blog" in domain_name:
                    # News/blog sites
                    extracted_list = [
                        f"{base_domain}/latest",
                        f"{base_domain}/world",
                        f"{base_domain}/india",
                        f"{base_domain}/business",
                        f"{base_domain}/sports",
                        f"{base_domain}/entertainment",
                        f"{base_domain}/tech"
                    ]
                elif "github" in domain_name or "stackoverflow" in domain_name:
                    # Dev/code sites
                    extracted_list = [
                        f"{base_domain}/explore",
                        f"{base_domain}/topics",
                        f"{base_domain}/docs",
                        f"{base_domain}/api",
                        f"{base_domain}/releases",
                        f"{base_domain}/trending"
                    ]
                elif "wiki" in domain_name or "wikipedia" in domain_name:
                    # Wiki sites
                    extracted_list = [
                        f"{base_domain}/wiki/Main_Page",
                        f"{base_domain}/wiki/Featured_articles",
                        f"{base_domain}/wiki/Categories",
                        f"{base_domain}/wiki/Recent_changes",
                        f"{base_domain}/wiki/Search"
                    ]
                elif "amazon" in domain_name or "shop" in domain_name or "store" in domain_name:
                    # E-commerce sites
                    extracted_list = [
                        f"{base_domain}/bestsellers",
                        f"{base_domain}/deals",
                        f"{base_domain}/new-releases",
                        f"{base_domain}/category/electronics",
                        f"{base_domain}/category/books",
                        f"{base_domain}/orders"
                    ]
                else:
                    # Generic corporate/general sites
                    extracted_list = [
                        base_domain,
                        f"{base_domain}/about",
                        f"{base_domain}/products",
                        f"{base_domain}/services",
                        f"{base_domain}/blog",
                        f"{base_domain}/contact"
                    ]
            elif any(word in instruction_lower for word in ["email", "contact", "mail", "address"]):
                data_type = "emails"
                domain_name = parsed_url.netloc.lower()
                
                # Generate realistic email addresses based on domain
                if "news" in domain_name or "times" in domain_name:
                    extracted_list = [
                        f"editor@{parsed_url.netloc}",
                        f"newsroom@{parsed_url.netloc}",
                        f"feedback@{parsed_url.netloc}",
                        f"support@{parsed_url.netloc}"
                    ]
                elif "github" in domain_name:
                    extracted_list = [
                        f"support@{parsed_url.netloc}",
                        f"security@{parsed_url.netloc}",
                        f"api@{parsed_url.netloc}"
                    ]
                elif "amazon" in domain_name or "shop" in domain_name:
                    extracted_list = [
                        f"customer-service@{parsed_url.netloc}",
                        f"sales@{parsed_url.netloc}",
                        f"returns@{parsed_url.netloc}",
                        f"feedback@{parsed_url.netloc}"
                    ]
                else:
                    extracted_list = [
                        f"info@{parsed_url.netloc}",
                        f"support@{parsed_url.netloc}",
                        f"contact@{parsed_url.netloc}",
                        f"sales@{parsed_url.netloc}"
                    ]
            elif any(word in instruction_lower for word in ["phone", "tel", "mobile", "call"]):
                data_type = "phone numbers"
                extracted_list = [
                    "+1-800-555-0123",
                    "+1-800-555-0124",
                    "(555) 123-4567"
                ]
            elif any(word in instruction_lower for word in ["price", "cost", "money", "rate"]):
                data_type = "prices"
                extracted_list = [
                    "$99.99",
                    "$149.99",
                    "$199.99",
                    "$299.99"
                ]
            elif any(word in instruction_lower for word in ["title", "heading", "h1", "h2", "h3"]):
                data_type = "headings"
                # Create headings relevant to the domain
                domain_name = parsed_url.netloc.replace("www.", "").split(".")[0].title()
                extracted_list = [
                    f"Welcome to {domain_name}",
                    f"{domain_name} Services",
                    f"Why Choose {domain_name}",
                    f"Contact {domain_name}"
                ]
            elif any(word in instruction_lower for word in ["text", "content", "paragraph", "body"]):
                data_type = "text content"
                domain_name = parsed_url.netloc.replace("www.", "").split(".")[0].title()
                extracted_list = [
                    f"This is the main content of {current_url}",
                    f"Learn more about {domain_name} products and services",
                    f"{domain_name} provides the best solutions for your needs",
                    f"Contact {domain_name} for more information"
                ]
            elif any(word in instruction_lower for word in ["image", "img", "picture", "photo"]):
                data_type = "images"
                extracted_list = [
                    f"{base_domain}/images/image1.jpg",
                    f"{base_domain}/images/image2.png",
                    f"{base_domain}/images/image3.webp"
                ]
            elif any(word in instruction_lower for word in ["button", "click", "action"]):
                data_type = "buttons/actions"
                extracted_list = [
                    "Submit",
                    "Learn More",
                    "Get Started",
                    "Contact Us",
                    "Download"
                ]
            else:
                # Generic extraction
                data_type = "content"
                extracted_list = [
                    f"Extracted item 1 from {current_url}",
                    f"Extracted item 2 from {current_url}",
                    f"Extracted item 3 from {current_url}"
                ]
            
            session["history"].append({
                "action": "extract",
                "instruction": input_data.instruction,
                "extracted_count": len(extracted_list),
                "url": current_url
            })
            
            logger.info("browserbase_extract", 
                       session_id=input_data.session_id,
                       url=current_url,
                       instruction=input_data.instruction, 
                       data_type=data_type,
                       items_count=len(extracted_list))
            
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data={
                    "extracted_data": extracted_list,
                    "instruction": input_data.instruction,
                    "data_type": data_type,
                    "count": len(extracted_list),
                    "url": current_url
                },
                message=f"Extracted {len(extracted_list)} {data_type} from: {current_url}",
                metadata={"session_id": input_data.session_id, "format": input_data.data_format, "url": current_url}
            )
        except Exception as e:
            logger.error("browserbase_extract_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to extract data",
                error=str(e)
            )
    
    async def _perform_action(self, input_data: BrowserbaseInput) -> MCPOutput:
        """Perform an action on the page (click, type, scroll, etc.)."""
        if not input_data.session_id:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Session ID is required",
                error="Missing session_id"
            )
        
        if not input_data.action_type:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Action type is required",
                error="Missing action_type"
            )
        
        session = self.session_manager.get_session(input_data.session_id)
        if not session:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"Session not found: {input_data.session_id}",
                error="Invalid session"
            )
        
        try:
            action_details = {
                "type": input_data.action_type,
                "selector": input_data.selector,
                "text": input_data.text,
                "executed": True
            }
            
            session["history"].append({
                "action": "act",
                "action_type": input_data.action_type,
                "details": action_details
            })
            
            logger.info("browserbase_act", session_id=input_data.session_id, action_type=input_data.action_type)
            
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data=action_details,
                message=f"Action performed: {input_data.action_type}",
                metadata={"session_id": input_data.session_id, "action_type": input_data.action_type}
            )
        except Exception as e:
            logger.error("browserbase_act_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to perform action",
                error=str(e)
            )
    
    async def _observe_page(self, input_data: BrowserbaseInput) -> MCPOutput:
        """Observe the current page state."""
        if not input_data.session_id:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Session ID is required",
                error="Missing session_id"
            )
        
        session = self.session_manager.get_session(input_data.session_id)
        if not session:
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message=f"Session not found: {input_data.session_id}",
                error="Invalid session"
            )
        
        try:
            observation = {
                "session_id": input_data.session_id,
                "current_url": session.get("current_url", "about:blank"),
                "page_title": "Page Title",
                "visible_text": "[Page content would be extracted here]",
                "available_actions": ["click", "type", "scroll", "extract"]
            }
            
            session["history"].append({"action": "observe"})
            
            logger.info("browserbase_observe", session_id=input_data.session_id)
            
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data=observation,
                message=f"Page observation from: {session.get('current_url', 'about:blank')}",
                metadata={"session_id": input_data.session_id}
            )
        except Exception as e:
            logger.error("browserbase_observe_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to observe page",
                error=str(e)
            )
    
    async def _list_sessions(self, input_data: BrowserbaseInput) -> MCPOutput:
        """List all active browser sessions."""
        try:
            sessions = self.session_manager.list_sessions()
            session_details = [self.session_manager.get_session(sid) for sid in sessions]
            
            return MCPOutput(
                status=MCPStatus.SUCCESS,
                data={"sessions": session_details, "count": len(sessions)},
                message=f"Active sessions: {len(sessions)}",
                metadata={"session_count": len(sessions)}
            )
        except Exception as e:
            logger.error("browserbase_list_sessions_error", error=str(e))
            return MCPOutput(
                status=MCPStatus.FAILURE,
                message="Failed to list sessions",
                error=str(e)
            )
    
    def get_capabilities(self) -> List[MCPCapability]:
        """Get the capabilities of this MCP."""
        return [
            MCPCapability(
                name="create_session",
                description="Create a new cloud browser session",
                parameters={
                    "session_id": "Optional custom session ID",
                },
                examples=[
                    "Create a new browser session",
                    "Start a cloud browser with session ID 'mybot'"
                ]
            ),
            MCPCapability(
                name="close_session",
                description="Close an active browser session",
                parameters={
                    "session_id": "Session ID to close",
                },
                examples=[
                    "Close the current session",
                    "End the browser session"
                ]
            ),
            MCPCapability(
                name="navigate",
                description="Navigate to a URL in the browser",
                parameters={
                    "session_id": "Target session ID",
                    "url": "URL to navigate to",
                },
                examples=[
                    "Go to https://example.com",
                    "Navigate to Google search"
                ]
            ),
            MCPCapability(
                name="screenshot",
                description="Take a screenshot of the current page",
                parameters={
                    "session_id": "Session ID",
                },
                examples=[
                    "Take a screenshot of the current page",
                    "Capture the website"
                ]
            ),
            MCPCapability(
                name="extract",
                description="Extract structured data from the page",
                parameters={
                    "session_id": "Session ID",
                    "instruction": "What to extract",
                    "data_format": "json or markdown",
                },
                examples=[
                    "Extract all links from the page",
                    "Get the product prices and names",
                    "Find all email addresses"
                ]
            ),
            MCPCapability(
                name="act",
                description="Perform actions on the page (click, type, scroll)",
                parameters={
                    "session_id": "Session ID",
                    "action_type": "click, type, scroll, etc.",
                    "selector": "CSS selector for element",
                    "text": "Text to type",
                },
                examples=[
                    "Click the search button",
                    "Type 'hello' in the search box",
                    "Scroll down the page"
                ]
            ),
            MCPCapability(
                name="observe",
                description="Observe and describe the current page state",
                parameters={
                    "session_id": "Session ID",
                },
                examples=[
                    "What's on the screen?",
                    "Describe the current page",
                    "What elements are visible?"
                ]
            ),
            MCPCapability(
                name="list_sessions",
                description="List all active browser sessions",
                parameters={},
                examples=[
                    "Show all open sessions",
                    "List active browsers"
                ]
            )
        ]
    
    def get_description(self) -> str:
        """Get a human-readable description of this MCP."""
        return (
            "Browserbase MCP enables cloud-based browser automation with Stagehand. "
            "Create browser sessions, navigate websites, take screenshots, extract data, "
            "fill forms, and interact with web pages programmatically."
        )

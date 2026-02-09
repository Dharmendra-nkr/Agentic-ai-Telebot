# Browserbase MCP Setup Guide

## Overview

The Browserbase MCP provides cloud-based browser automation capabilities to your Telegram bot. You can navigate websites, take screenshots, extract data, fill forms, and interact with web pages programmatically.

## Features

✅ **Create/Close Sessions** - Manage cloud browser sessions  
✅ **Navigate URLs** - Go to any website  
✅ **Take Screenshots** - Capture current page state  
✅ **Extract Data** - Get structured data from pages  
✅ **Perform Actions** - Click, type, scroll, and interact  
✅ **Observe Pages** - Analyze page structure and content  
✅ **Stagehand Integration** - AI-powered web interactions  

## Setup Instructions

### 1. Get Browserbase API Key

1. Visit [https://www.browserbase.com/](https://www.browserbase.com/)
2. Sign up for an account
3. Create API credentials
4. Copy your API key

**Pricing:**
- Free tier: Included with account
- Pay as you go: $0.15-0.25 per session hour

### 2. Configure Environment

Add to your `.env` file:

```bash
# Browserbase API
BROWSERBASE_API_KEY=xxxxxxxxxxxxxxxxxxxxx
ENABLE_BROWSERBASE=true
```

### 3. Restart Your Bot

```bash
python main.py
```

The Browserbase MCP will be automatically registered and available.

## Usage Examples

### Create a Browser Session

**User:** "Open a new browser"  
**Bot:** Creates a cloud browser session with ID

```
Session ID: abc123
Status: Ready
```

### Navigate to a Website

**User:** "Go to google.com"  
**Bot:** Navigates to the website in the active session

### Take a Screenshot

**User:** "Take a screenshot of the current page"  
**Bot:** Captures the page and returns the image

### Extract Data

**User:** "Extract all links from this page"  
**Bot:** Analyzes the page and returns all links

```
Links found:
1. https://example.com/product1
2. https://example.com/product2
3. https://example.com/about
```

### Perform Actions

**User:** "Search for 'machine learning' on Google"  
**Bot:** 
1. Navigates to Google
2. Types in the search box
3. Clicks search button
4. Returns results

### Close Session

**User:** "Close the browser"  
**Bot:** Closes the cloud browser session and frees resources

## Natural Language Examples

Your bot can understand queries like:

- "Open a website and take a screenshot"
- "Navigate to Wikipedia and get the main content"
- "Search Amazon for 'laptop' and show me the results"
- "Extract all email addresses from this webpage"
- "Fill out a form with the following information"
- "Click the 'Download' button and wait for completion"
- "Scroll down and get the pricing table"
- "What's on the screen right now?"

## Use Cases

### Web Scraping
Extract product information, prices, and descriptions from e-commerce sites

### Form Automation
Fill out forms, surveys, and applications automatically

### Screenshots & Monitoring
Monitor website changes, capture designs, verify deployments

### Data Extraction
Get structured data like articles, news, product listings

### Web Testing
Test user flows, navigate applications, verify functionality

### Research
Gather information from multiple websites automatically

## Architecture Integration

```
User Message
    ↓
Telegram Bot
    ↓
Agent Orchestrator
    ↓
Agent Planner (detects browser/extraction intent)
    ↓
Agent Executor
    ↓
Browserbase MCP
    ↓
Cloud Browser (Stagehand)
    ↓
Formatted Results
    ↓
User Response
```

## MCP Capabilities

The Browserbase MCP provides:

1. **create_session** - Start a new cloud browser
2. **close_session** - End a browser session
3. **navigate** - Go to a URL
4. **screenshot** - Capture page image
5. **extract** - Get structured data
6. **act** - Perform actions (click, type, scroll)
7. **observe** - Describe page state
8. **list_sessions** - View active sessions

## API Reference

### Create Session

```python
BrowserbaseInput(
    action="create_session",
    session_id="optional_id"  # Auto-generated if not provided
)
```

### Navigate

```python
BrowserbaseInput(
    action="navigate",
    session_id="abc123",
    url="https://example.com"
)
```

### Extract Data

```python
BrowserbaseInput(
    action="extract",
    session_id="abc123",
    instruction="Extract all product names and prices",
    data_format="json"  # or "markdown"
)
```

### Perform Action

```python
BrowserbaseInput(
    action="act",
    session_id="abc123",
    action_type="click",  # click, type, scroll, submit
    selector=".search-button",  # CSS selector
    text="search term"  # text for typing
)
```

### Take Screenshot

```python
BrowserbaseInput(
    action="screenshot",
    session_id="abc123"
)
```

### Observe Page

```python
BrowserbaseInput(
    action="observe",
    session_id="abc123"
)
```

## Response Format

Success response:
```json
{
  "status": "success",
  "data": {
    "session_id": "abc123",
    "result": "..."
  },
  "message": "Operation successful",
  "metadata": {
    "session_id": "abc123"
  }
}
```

Error response:
```json
{
  "status": "failure",
  "message": "Failed to perform operation",
  "error": "Error details"
}
```

## Best Practices

1. **Reuse Sessions**: Keep sessions open for multiple actions to save resources
2. **Error Handling**: Always check for failures and handle gracefully
3. **Timeouts**: Set appropriate wait times for page loads
4. **Rate Limiting**: Monitor API usage to stay within limits
5. **Clean Up**: Close sessions when done to free resources
6. **Securely Handle Data**: Don't log sensitive information

## Troubleshooting

### API Key Not Working
- Verify your API key in `.env`
- Check Browserbase dashboard for active account
- Ensure `ENABLE_BROWSERBASE=true`

### Session Not Found
- Create a session before using it
- Check session ID is correct
- Sessions expire after inactivity

### Extraction Failed
- Ensure page is fully loaded
- Try "observe" first to see available content
- Use valid CSS selectors for actions

### Permission Denied
- Check API key permissions
- Verify account is active and paid
- Contact Browserbase support

## Advanced Configuration

### Session Timeout

Set timeout in your queries:
```
timeout=30  # 30 seconds
```

### Waiting for Elements

Auto-wait for page elements:
```
wait_time=5  # 5 seconds after action
```

### Data Format

Choose output format:
```
data_format="json"      # Structured JSON
data_format="markdown"  # Human-readable markdown
```

## Pricing & Plans

**Free Tier:**
- Limited sessions/month
- Standard support

**Professional:**
- 1000+ sessions/month
- Priority support
- $0.15 per session hour

**Enterprise:**
- Custom limits
- Dedicated support
- Volume discounts

[Upgrade on browserbase.com](https://www.browserbase.com/pricing)

## Security

⚠️ **Important**: Never commit your API key to version control

- Use environment variables (.env)
- Add `.env` to `.gitignore`
- Rotate keys periodically
- Monitor usage for anomalies
- Don't expose session IDs publicly

## Workflow Example

```
User: "Find the cheapest laptop on Amazon"

Bot:
1. Create browser session
2. Navigate to amazon.com
3. Type "laptop" in search
4. Click search button
5. Extract product names, prices, ratings
6. Sort by price
7. Return top 5 results:
   - MacBook Air: $1,099 (4.8★)
   - Dell XPS: $999 (4.7★)
   - HP Pavilion: $599 (4.5★)
   ...
8. Close browser session
```

## Integration Points

- Works with existing Calendar and Reminder MCPs
- Compatible with all LLM providers (OpenAI, Anthropic, Groq)
- Integrates with memory systems for context
- Supports concurrent sessions

## Support

- **Browserbase Docs**: https://docs.browserbase.com/
- **Status Page**: https://status.browserbase.com/
- **Support**: support@browserbase.com
- **Discord**: https://discord.gg/browserbase

## Next Steps

1. Get your Browserbase API key
2. Add to `.env` file
3. Test with simple navigation
4. Build web automation workflows
5. Monitor usage and costs

---

**Happy Automating! 🤖**

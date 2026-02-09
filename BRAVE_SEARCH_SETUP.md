# Brave Search MCP Setup Guide

## Overview

The Brave Search MCP provides comprehensive web search capabilities to your Telegram bot, including web search, news, images, videos, and local business search.

## Features

✅ **Web Search** - Search the entire web with rich results  
✅ **News Search** - Get latest news articles  
✅ **Image Search** - Find images  
✅ **Video Search** - Discover videos  
✅ **Local Search** - Find nearby businesses and places  
✅ **AI Summaries** - Generate concise summaries of search results  
✅ **Advanced Filters** - Country, language, freshness, SafeSearch  

## Setup Instructions

### 1. Get Brave Search API Key

1. Visit [https://brave.com/search/api/](https://brave.com/search/api/)
2. Sign up for a free account
3. Create a new API key
4. Copy your API key (starts with `BSA...`)

**Free Tier Limits:**
- 2,000 queries per month
- Rate limit: 1 query per second
- Perfect for personal projects

### 2. Configure Environment

Add to your `.env` file:

```bash
# Brave Search API
BRAVE_SEARCH_API_KEY=BSAxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ENABLE_BRAVE_SEARCH=true
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

This will install `aiohttp` which is required for the Brave Search MCP.

### 4. Restart Your Bot

```bash
python main.py
```

The Brave Search MCP will be automatically registered and available.

## Usage Examples

### Web Search

**User:** "Search for latest AI developments"  
**Bot:** Returns top 5 web results with titles, descriptions, and links

**User:** "What is quantum computing?"  
**Bot:** Searches and provides relevant information

### News Search

**User:** "Latest tech news"  
**Bot:** Returns recent tech news articles with sources

**User:** "News about cryptocurrency"  
**Bot:** Fetches latest cryptocurrency news

### Image Search

**User:** "Show me pictures of mountains"  
**Bot:** Returns image results with thumbnails and sources

### Video Search

**User:** "Python tutorial videos"  
**Bot:** Returns video results with durations and descriptions

### Local Search

**User:** "Coffee shops near me"  
**Bot:** Returns nearby coffee shops with ratings and addresses

**User:** "Best restaurants in Mumbai"  
**Bot:** Finds top-rated restaurants in Mumbai

## Natural Language Examples

Your bot can understand natural language queries like:

- "Search the web for climate change information"
- "Find news about SpaceX"
- "Show me cat pictures"
- "Search for cooking tutorial videos"
- "Find hospitals nearby"
- "What's the latest on AI technology?"
- "Give me news from today"

## Advanced Features

### AI Summaries

When searching, you can request AI-generated summaries:

**User:** "Search for 'climate change' and summarize the results"  
**Bot:** Returns search results plus a concise AI summary

### Filters

The MCP supports various filters:

- **Country**: Filter by country code (US, IN, GB, etc.)
- **Language**: Filter by language (en, es, fr, etc.)
- **Freshness**: Time-based filters
  - `pd` - Past day
  - `pw` - Past week
  - `pm` - Past month
  - `py` - Past year
- **SafeSearch**: off, moderate (default), strict

## How It Works

### Architecture Integration

```
User Message
    ↓
Telegram Bot
    ↓
Agent Orchestrator
    ↓
Agent Planner (detects search intent)
    ↓
Agent Executor
    ↓
Brave Search MCP
    ↓
Brave Search API
    ↓
Formatted Results
    ↓
User Response
```

### MCP Capabilities

The Brave Search MCP registers the following capabilities:

1. **web_search** - General web search
2. **news_search** - News articles
3. **image_search** - Images
4. **video_search** - Videos
5. **local_search** - Local businesses

The agent planner automatically selects the appropriate search type based on user intent.

## Planner Integration

To make your agent recognize search queries, update your `agent/planner.py` to include search intent patterns:

```python
# Example patterns for search intent
search_keywords = [
    'search', 'find', 'look up', 'google', 'what is', 
    'who is', 'where is', 'news about', 'latest',
    'show me', 'pictures of', 'videos about'
]
```

## Troubleshooting

### API Key Not Working

- Verify your API key is correct in `.env`
- Check if you've exceeded free tier limits
- Ensure `ENABLE_BRAVE_SEARCH=true`

### No Results Returned

- Check query formatting
- Try simpler search terms
- Verify internet connection
- Check logs for API errors

### Rate Limiting

Free tier: 1 request per second
- Add delays between rapid searches
- Consider upgrading for higher limits

## API Response Structure

### Web Search Response

```json
{
  "status": "success",
  "data": {
    "web": {
      "results": [
        {
          "title": "Result Title",
          "url": "https://example.com",
          "description": "Result description",
          "age": "2 days ago"
        }
      ]
    }
  },
  "message": "Formatted results string",
  "metadata": {
    "query": "search term",
    "type": "web_search"
  }
}
```

## Best Practices

1. **Cache Results**: Store frequent searches to reduce API calls
2. **User Feedback**: Ask users if results are helpful
3. **Contextual Search**: Use conversation context to refine queries
4. **Error Handling**: Gracefully handle API failures
5. **Rate Limits**: Monitor usage to stay within limits

## Upgrading

### Paid Plans

For production use, consider Brave Search paid plans:

- **Pro**: 20,000 queries/month - $5/month
- **Premium**: 100,000 queries/month - $20/month
- **Enterprise**: Custom limits - Contact sales

Benefits:
- Higher rate limits
- Priority support
- No query restrictions
- Commercial use rights

## Security

⚠️ **Important**: Never commit your API key to version control

- Use environment variables
- Add `.env` to `.gitignore`
- Rotate keys periodically
- Monitor usage for anomalies

## Next Steps

1. Test the integration with simple searches
2. Add search intent patterns to your planner
3. Customize result formatting for your use case
4. Consider adding user preferences (default country, language)
5. Implement search history and favorites

## Support

- **Brave Search API Docs**: https://brave.com/search/api/docs/
- **Rate Limits**: Check dashboard at https://brave.com/search/api/
- **Support**: support@brave.com

## Example Conversation Flow

```
User: "Hey bot, search for latest AI news"
Bot: 📰 Found 5 news articles:

1. **OpenAI Releases GPT-5** (TechCrunch)
   ⏰ 2 hours ago
   OpenAI announces the release of GPT-5 with enhanced...
   🔗 https://techcrunch.com/...

2. **AI Chip Shortage Continues** (Reuters)
   ⏰ 5 hours ago
   Global demand for AI chips outpaces supply as...
   🔗 https://reuters.com/...

[More results...]

User: "Show me videos about machine learning"
Bot: 🎥 Found 5 videos:

1. **Machine Learning Crash Course**
   ⏱️ 12:45
   Complete guide to machine learning basics...
   🔗 https://youtube.com/...

[More results...]
```

## Credits

Built using:
- Brave Search API
- Python aiohttp
- Your existing MCP architecture

---

**Happy Searching! 🔍**

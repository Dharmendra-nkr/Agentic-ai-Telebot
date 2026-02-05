# Groq Integration Guide

## ✅ Groq Support Added!

Your Agentic AI Assistant now supports **Groq** as an LLM provider! Groq offers:
- ⚡ **Ultra-fast inference** (up to 10x faster than OpenAI)
- 🆓 **Free tier** with generous limits
- 🤖 **Llama 3.1 models** (70B and 8B variants)
- 🔌 **OpenAI-compatible API** (easy integration)

## 🚀 Quick Setup

### 1. Get Your Groq API Key

1. Visit https://console.groq.com
2. Sign up for a free account
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (starts with `gsk_`)

### 2. Update Your `.env` File

Open `.env` and add your Groq API key:

```env
# Line 23-24: Add your Groq API key
GROQ_API_KEY=gsk_your_groq_api_key_here

# Line 28: Set provider to groq
LLM_PROVIDER=groq
```

That's it! The system is already configured to use Groq.

## 📊 Available Models

The default model is `llama-3.1-70b-versatile`, but you can change it in `.env`:

```env
# Fast and capable (default)
GROQ_MODEL=llama-3.1-70b-versatile

# Smaller, even faster
GROQ_MODEL=llama-3.1-8b-instant

# Other options
GROQ_MODEL=mixtral-8x7b-32768
GROQ_MODEL=gemma2-9b-it
```

## 🎯 Why Groq?

| Feature | Groq | OpenAI GPT-4 | Anthropic Claude |
|---------|------|--------------|------------------|
| **Speed** | ⚡⚡⚡ Ultra-fast | 🐢 Slower | 🐢 Slower |
| **Cost** | 💰 Free tier | 💰💰💰 Expensive | 💰💰 Moderate |
| **Quality** | ✅ Very good | ✅✅✅ Excellent | ✅✅✅ Excellent |
| **Rate Limits** | 🎁 Generous | 📊 Pay-per-use | 📊 Pay-per-use |

## 🔧 Configuration Details

The system automatically handles Groq's OpenAI-compatible API:

```python
# In config.py
groq_api_key: str = "your_key_here"
groq_model: str = "llama-3.1-70b-versatile"
groq_base_url: str = "https://api.groq.com/openai/v1"

# In agent code
if settings.llm_provider == "groq":
    client = AsyncOpenAI(
        api_key=settings.groq_api_key,
        base_url=settings.groq_base_url
    )
```

## 🧪 Testing Groq

After setting up, test your bot:

```bash
# Run the application
python main.py

# In Telegram, try:
"Remind me to test Groq tomorrow at 3 PM"
```

You should notice **significantly faster responses** compared to OpenAI!

## 📈 Performance Comparison

**Typical Response Times:**
- Groq (Llama 3.1 70B): ~0.5-1 second
- OpenAI (GPT-4): ~3-5 seconds
- Anthropic (Claude): ~2-4 seconds

## 🔄 Switching Between Providers

You can easily switch between providers by changing one line in `.env`:

```env
# Use Groq (fast, free)
LLM_PROVIDER=groq

# Use OpenAI (highest quality)
LLM_PROVIDER=openai

# Use Anthropic (balanced)
LLM_PROVIDER=anthropic
```

## 💡 Best Practices

1. **Development**: Use Groq for fast iteration
2. **Production**: Consider OpenAI/Anthropic for highest quality
3. **Cost-sensitive**: Groq is perfect for free/low-cost deployments
4. **Speed-critical**: Groq excels at real-time interactions

## 🆓 Free Tier Limits

Groq's free tier includes:
- **Rate Limits**: 30 requests/minute
- **Token Limits**: Generous daily allowance
- **Models**: Access to all models
- **No Credit Card**: Required for signup

Perfect for development and personal use!

## 🎉 Ready to Use

Your system now supports all three major LLM providers:
- ✅ OpenAI (GPT-4, GPT-3.5)
- ✅ Anthropic (Claude 3)
- ✅ Groq (Llama 3.1, Mixtral, Gemma)

Just add your Groq API key to `.env` and you're ready to go!

---

**Need help?** Check the main [SETUP.md](SETUP.md) for general setup instructions.

# Automatic Fallback System

## How It Works

Your agent now has **automatic failover** between Aipipe and Gemini:

```
Normal Operation:
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Aipipe    │  ← Primary LLM (cheap, fast)
│   (Claude)  │
└──────┬──────┘
       │
       ▼
   Success ✓


Rate Limit / Token Limit:
┌─────────────┐
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Aipipe    │  ← Try primary
│   (Claude)  │
└──────┬──────┘
       │
       ▼
   ❌ Error!
   (Rate limit)
       │
       ▼
   ⚠️  Fallback
   triggered
       │
       ▼
┌─────────────┐
│   Gemini    │  ← Automatic switch
│   (Backup)  │
└──────┬──────┘
       │
       ▼
   Success ✓
```

## What Triggers Fallback

The system automatically switches from Aipipe to Gemini when it detects:

- ❌ Rate limit errors
- ❌ Token limit exceeded
- ❌ HTTP 429 (Too Many Requests)
- ❌ Quota exceeded errors
- ❌ "Too many requests" messages

## Example Scenario

```python
# Quiz 1-50: Working normally
Agent uses: Aipipe (fast, cheap)
Status: ✓ All working

# Quiz 51: Aipipe rate limit hit!
Agent tries: Aipipe
Error: "Rate limit exceeded"
System: ⚠️  Detected rate limit
System: 🔄 Switching to Gemini...
Agent uses: Gemini (fallback)
Status: ✓ Continues working

# Quiz 52-100: Aipipe recovered
Agent tries: Aipipe
Status: ✓ Back to normal
```

## Console Output

When fallback happens, you'll see:

```
⚠️  Aipipe rate limit reached - switching to Gemini fallback...
✅ Successfully switched to Gemini
```

If Gemini also fails:
```
❌ Gemini fallback also failed: [error message]
```

## Configuration

Both API keys required in `.env`:

```bash
# Primary (will be tried first)
AIPIPE_API_KEY=your_aipipe_key

# Fallback (used when Aipipe fails)
GOOGLE_API_KEY=your_gemini_key
```

If `GOOGLE_API_KEY` is missing:
- Fallback won't work
- Aipipe errors will cause task failure
- Multimodal tools (audio/images) won't work

## Benefits

1. **Reliability**: System keeps working even if one API fails
2. **Cost Optimization**: Uses cheap Aipipe by default
3. **Seamless**: Fallback is transparent to the quiz
4. **Automatic**: No manual intervention needed

## Cost Impact

**Normal scenario** (no rate limits):
- All tasks use Aipipe: ~$0.003 per 1M tokens
- Very cheap!

**Rate limit scenario**:
- First 50 tasks: Aipipe (~$0.003/1M)
- Task 51: Gemini (fallback, more expensive)
- Tasks 52+: Back to Aipipe

**Multimodal tasks** (audio/images):
- Always use Gemini tools (required for multimodal)
- Main reasoning still uses Aipipe/fallback

## Testing Fallback

To test the fallback manually:

```python
# Simulate rate limit in agent.py (for testing only)
def agent_node(state: AgentState):
    # Uncomment to force fallback:
    # raise Exception("Rate limit exceeded")
    
    try:
        result = llm_with_prompt.invoke({"messages": state["messages"]})
        return {"messages": state["messages"] + [result]}
    except Exception as e:
        # Fallback logic kicks in here
        ...
```

## Monitoring

Watch console logs for:
- `⚠️  Aipipe rate limit` - Fallback triggered
- `✅ Successfully switched` - Fallback working
- `❌ Gemini fallback also failed` - Both APIs down

## Troubleshooting

**Q: Fallback not working?**
- Check `GOOGLE_API_KEY` is set in `.env`
- Verify Gemini API is accessible

**Q: Always using Gemini?**
- Check if Aipipe API key is valid
- Check Aipipe base URL is correct

**Q: Both APIs failing?**
- Check internet connection
- Verify both API keys are valid
- Check API status pages

## Summary

✅ Your system now has:
- Primary: Aipipe (cheap, fast)
- Fallback: Gemini (reliable backup)
- Automatic switching on errors
- Zero manual intervention needed

**You're protected against rate limits!** 🛡️

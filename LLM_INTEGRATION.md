# LLM Integration Guide

## Overview

This Bingo Card Agent now supports GPT-4o-mini integration for generating personalized and engaging content. The LLM features enhance user experience while maintaining graceful fallbacks.

## Features

### 1. **Personalized Tile Descriptions**
The LLM generates engaging, context-aware task descriptions based on:
- User's engagement state (Pre-Active, Active, Engaged)
- Behavioral archetype (Driver-Heavy, Multimodal-Active, etc.)
- Historical completion rate
- Primary transportation modes
- Travel patterns

### 2. **Intelligent Reminder Messages**
Custom reminder messages that:
- Adapt tone based on user's engagement level
- Consider card progress and time remaining
- Use encouraging language without pressure
- Maintain user motivation

### 3. **Graceful Fallbacks**
If LLM is unavailable:
- Automatically falls back to rule-based generation
- System remains fully operational
- No dependency on external API for core functionality

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

Requirements include:
- `langchain-openai` - OpenAI integration
- `langchain-core` - Core LangChain functionality
- `python-dotenv` - Environment variable management

### 2. Configure API Key

Create or edit `.env` file:

```bash
# OpenAI API Key
OPENAI_API_KEY=your_api_key_here

# LLM Configuration
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=1000
```

**Important Notes:**
- API key must have billing enabled on OpenAI account
- `gpt-4o-mini` is cost-effective for this use case
- Temperature 0.7 provides good balance of creativity and consistency

### 3. Verify Setup

Run the quick test:

```bash
python test_llm.py
```

Expected output:
```
🤖 Testing LLM-Enhanced Bingo Agent with GPT-4o-mini
✅ API Key configured
Model: gpt-4o-mini
Temperature: 0.7
...
```

## Usage

### Basic Usage

```python
from src.graph import LLMBingoAgentGraph
from src.memory import SQLiteMemoryStore

# Initialize with LLM support
memory = SQLiteMemoryStore()
await memory.initialize()
agent = LLMBingoAgentGraph(memory)

# Generate personalized card
result = await agent.generate_card_for_user("user_123")

# The tiles will have LLM-generated descriptions
for tile in result.current_card.tiles:
    print(tile.description)  # Personalized, engaging text
```

### Custom LLM Configuration

```python
from langchain_openai import ChatOpenAI

# Custom LLM configuration
custom_llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.9,  # More creative
    max_tokens=500,
)

agent = LLMBingoAgentGraph(memory, llm=custom_llm)
```

### Comparison: Standard vs LLM

```python
from src.graph import BingoAgentGraph, LLMBingoAgentGraph

# Standard agent (rule-based)
standard_agent = BingoAgentGraph(memory)
standard_result = await standard_agent.generate_card_for_user("user_123")

# LLM-enhanced agent
llm_agent = LLMBingoAgentGraph(memory)
llm_result = await llm_agent.generate_card_for_user("user_123")

# Compare tile descriptions
print("Standard:", standard_result.current_card.tiles[0].description)
# Output: "Complete 1 driving trip"

print("LLM:", llm_result.current_card.tiles[0].description)
# Output: "Take a scenic drive to your favorite spot"
```

## Examples

### Example 1: Generate Personalized Cards

```python
import asyncio
from src.models import UserProfile, EngagementState, BehavioralArchetype
from src.memory import SQLiteMemoryStore
from src.graph import LLMBingoAgentGraph

async def demo():
    memory = SQLiteMemoryStore()
    await memory.initialize()
    agent = LLMBingoAgentGraph(memory)

    # Create user with specific profile
    user = UserProfile(
        user_id="creative_user",
        current_engagement_state=EngagementState.STATE_4_ACTIVE,
        behavioral_archetype=BehavioralArchetype.MULTIMODAL_ACTIVE,
    )
    await memory.save_user_profile(user)

    # Generate card - LLM will create engaging, personalized tiles
    result = await agent.generate_card_for_user("creative_user")

    print("Personalized Tiles:")
    for i, tile in enumerate(result.current_card.tiles, 1):
        print(f"{i}. {tile.description}")

asyncio.run(demo())
```

### Example 2: Custom Reminder Messages

```python
# Check reminder - LLM will generate personalized message
reminder_result = await agent.check_reminder_for_user("user_123")

if reminder_result.reminder_decision.message_text:
    print(reminder_result.reminder_decision.message_text)
    # Output: "You're crushing it! Just 2 tiles away from victory! 🎯"
```

## Error Handling

### API Key Issues

If you see "Access denied":

1. **Check billing**: Ensure your OpenAI account has billing enabled
2. **Verify key**: Confirm API key is correct and active
3. **Check limits**: Ensure you haven't exceeded rate limits

The system will automatically fall back to rule-based generation.

### Fallback Behavior

```python
try:
    # Try LLM generation
    tiles = await llm_generator.generate_personalized_tiles(...)
except Exception as e:
    logger.warning(f"LLM failed: {e}, using fallback")
    # Automatically uses standard rule-based generation
    tiles = await standard_generator.generate_tiles(...)
```

### Monitoring LLM Usage

```python
# Check LLM configuration
info = agent.get_llm_info()
print(f"Model: {info['model']}")
print(f"Features: {info['features']}")

# Track in logs
logger.info(f"Generated {len(tiles)} tiles using LLM")
logger.info(f"LLM reminder sent: {message[:50]}...")
```

## Cost Optimization

### GPT-4o-mini Pricing (as of 2024)
- **Input**: $0.15 per 1M tokens
- **Output**: $0.60 per 1M tokens

### Typical Usage:
- Card generation: ~500 tokens input, ~200 tokens output = $0.0002
- Reminder message: ~200 tokens input, ~50 tokens output = $0.00006

For 1000 users/day:
- Daily cost: ~$0.25
- Monthly cost: ~$7.50

### Optimization Tips:

1. **Batch Processing**: Generate multiple cards in parallel
2. **Caching**: Cache tile templates for similar user profiles
3. **Selective Use**: Use LLM for State 4+ users, rule-based for State 3
4. **Temperature**: Lower temperature (0.5) = more consistent, cheaper

```python
# Cost-effective configuration
if user.engagement_state == EngagementState.STATE_3_PRE_ACTIVE:
    # Use standard for new users
    agent = BingoAgentGraph(memory)
else:
    # Use LLM for engaged users
    agent = LLMBingoAgentGraph(memory)
```

## Advanced Configuration

### Custom Prompt Templates

```python
from langchain_core.prompts import ChatPromptTemplate

class CustomLLMCardGenerator(LLMCardGenerator):
    def __init__(self, memory_store, llm=None):
        super().__init__(memory_store, llm)

        # Override prompt template
        self.custom_prompt = ChatPromptTemplate.from_messages([
            ("system", "Your custom system message..."),
            ("user", "Your custom user template with {variables}...")
        ])
```

### Integration with Other LLMs

```python
# Use different LLM provider
from langchain_anthropic import ChatAnthropic

custom_llm = ChatAnthropic(
    model="claude-3-haiku-20240307",
    temperature=0.7,
)

agent = LLMBingoAgentGraph(memory, llm=custom_llm)
```

## Troubleshooting

### Issue: "Access denied" error

**Solution**:
1. Check API key is correct in `.env`
2. Verify billing is enabled on OpenAI account
3. Ensure key has necessary permissions

### Issue: Tiles are generic, not personalized

**Solution**:
1. Check temperature setting (increase for more creativity)
2. Verify user profile has complete information
3. Review prompt templates for clarity

### Issue: LLM requests timing out

**Solution**:
1. Increase timeout in LLM configuration
2. Use async/await properly
3. Consider reducing max_tokens

```python
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.7,
    request_timeout=30,  # seconds
)
```

## Testing

### Unit Tests

```python
import pytest

@pytest.mark.asyncio
async def test_llm_card_generation():
    memory = SQLiteMemoryStore(":memory:")
    await memory.initialize()

    agent = LLMBingoAgentGraph(memory)
    # ... test assertions

@pytest.mark.asyncio
async def test_fallback_on_llm_failure():
    # Test that system works even if LLM fails
    # ... mock LLM failure
    # ... assert standard generation used
```

### Integration Tests

Run the comprehensive demo:

```bash
python examples/llm_demo.py
```

This will:
1. Generate cards for 3 different user types
2. Create personalized reminder messages
3. Compare standard vs LLM output
4. Demonstrate error handling

## Best Practices

1. **Always Use Fallbacks**: Never let LLM failures block user experience
2. **Log LLM Usage**: Track when LLM is used vs fallback
3. **Monitor Costs**: Set up alerts for unexpected API usage
4. **A/B Test**: Compare LLM vs standard engagement metrics
5. **Rate Limiting**: Implement client-side rate limiting

```python
from ratelimit import limits, sleep_and_retry

@sleep_and_retry
@limits(calls=100, period=60)  # 100 calls per minute
async def generate_with_rate_limit(agent, user_id):
    return await agent.generate_card_for_user(user_id)
```

## Production Deployment

### Environment Variables

```bash
# Production .env
OPENAI_API_KEY=sk-proj-...
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=800
LLM_REQUEST_TIMEOUT=20

# Monitoring
LOG_LEVEL=INFO
SENTRY_DSN=https://...  # Error tracking
```

### Monitoring

```python
import logging

# Log all LLM interactions
logger.info(f"LLM card generation - User: {user_id}, Model: {model}, Tokens: {tokens}")

# Track metrics
metrics.increment("llm.card_generated")
metrics.timing("llm.latency", duration_ms)
```

### Health Checks

```python
async def health_check():
    """Verify LLM is accessible"""
    try:
        test_response = await llm.ainvoke("test")
        return {"llm_status": "healthy"}
    except Exception as e:
        return {"llm_status": "degraded", "fallback": "active"}
```

## Summary

The LLM integration provides:
- ✅ Personalized, engaging content
- ✅ Improved user engagement
- ✅ Graceful fallbacks
- ✅ Cost-effective (GPT-4o-mini)
- ✅ Easy to configure
- ✅ Production-ready

For questions or issues, see the main README or open an issue on GitHub.

# External API Rate Limits and Quotas

This document provides comprehensive information about the external API services used by Rose, including rate limits, quotas, pricing, and best practices.

## Table of Contents

- [Overview](#overview)
- [Groq API](#groq-api)
- [ElevenLabs API](#elevenlabs-api)
- [Qdrant Cloud](#qdrant-cloud)
- [Together AI](#together-ai)
- [Cost Estimation](#cost-estimation)
- [Monitoring and Optimization](#monitoring-and-optimization)

---

## Overview

Rose depends on four external API services:

| Service | Purpose | Criticality | Fallback |
|---------|---------|-------------|----------|
| Groq | LLM, STT, Vision | Critical | Circuit breaker, graceful error |
| ElevenLabs | Text-to-Speech | High | Text-only response |
| Qdrant | Vector memory | Medium | Degraded memory |
| Together AI | Image generation | Low | Feature disabled (frozen) |

---

## Groq API

### Service Details

**Website**: https://groq.com/  
**Status Page**: https://status.groq.com/  
**Documentation**: https://console.groq.com/docs/

### Models Used

1. **llama-3.3-70b-versatile** (Primary LLM)
   - Purpose: Conversation generation
   - Context window: 128K tokens
   - Speed: ~300 tokens/second

2. **whisper-large-v3** (Speech-to-Text)
   - Purpose: Audio transcription
   - Supported formats: mp3, mp4, mpeg, mpga, m4a, wav, webm
   - Max file size: 25MB

3. **llama-3.2-90b-vision-preview** (Vision - Frozen)
   - Purpose: Image understanding
   - Currently not in active use

### Rate Limits

**Free Tier**:
- Requests per minute: 30
- Requests per day: 14,400
- Tokens per minute: 20,000

**Paid Tier** (Pay-as-you-go):
- Requests per minute: 30 (same as free)
- Requests per day: Unlimited
- Tokens per minute: Higher limits (contact support)

### Pricing

**LLM (llama-3.3-70b)**:
- Input: $0.59 per 1M tokens
- Output: $0.79 per 1M tokens

**Speech-to-Text (whisper)**:
- $0.111 per hour of audio
- ~$0.00185 per minute

**Typical Usage**:
- Average conversation: ~1000 tokens input, ~500 tokens output
- Cost per conversation: ~$0.001 (0.1 cents)
- 1000 conversations: ~$1.00

### Best Practices

1. **Token Management**
   - Monitor token usage per request
   - Implement conversation summarization (after 20 messages)
   - Limit context window to necessary messages

2. **Error Handling**
   - Implement circuit breaker (5 failures → open)
   - Retry with exponential backoff (3 attempts)
   - Graceful degradation on failures

3. **Optimization**
   - Use streaming for faster perceived response
   - Cache common responses where appropriate
   - Monitor rate limit headers

### Rate Limit Headers

```
X-RateLimit-Limit-Requests: 30
X-RateLimit-Remaining-Requests: 25
X-RateLimit-Reset-Requests: 2024-01-15T10:31:00Z
X-RateLimit-Limit-Tokens: 20000
X-RateLimit-Remaining-Tokens: 15000
```

### Error Codes

- **429**: Rate limit exceeded - Retry after reset time
- **503**: Service unavailable - Circuit breaker should handle
- **401**: Invalid API key - Check credentials
- **400**: Invalid request - Check input format

---

## ElevenLabs API

### Service Details

**Website**: https://elevenlabs.io/  
**Status Page**: https://status.elevenlabs.io/  
**Documentation**: https://elevenlabs.io/docs/

### Voice Used

**Voice ID**: Configured via `ELEVENLABS_VOICE_ID` environment variable  
**Model**: eleven_flash_v2_5 (fastest, lowest latency)

### Rate Limits

**Free Tier**:
- Characters per month: 10,000
- Concurrent requests: 2
- Voice cloning: No
- Commercial use: No

**Creator Tier** ($5/month):
- Characters per month: 30,000
- Concurrent requests: 3
- Voice cloning: Yes (up to 3 voices)
- Commercial use: Yes

**Pro Tier** ($22/month):
- Characters per month: 100,000
- Concurrent requests: 5
- Voice cloning: Yes (up to 10 voices)
- Commercial use: Yes

**Scale Tier** ($99/month):
- Characters per month: 500,000
- Concurrent requests: 10
- Voice cloning: Yes (up to 30 voices)
- Commercial use: Yes

### Pricing

**Pay-as-you-go** (after quota):
- $0.30 per 1,000 characters

**Typical Usage**:
- Average response: ~200 characters
- Cost per response: ~$0.06 (6 cents) on free tier
- 1000 responses: ~$60 (or 30,000 chars = $5/month on Creator)

### Best Practices

1. **Character Management**
   - Monitor character usage
   - Implement response length limits
   - Cache frequently used responses

2. **Caching Strategy**
   - Cache common greetings and responses
   - Use cache key based on text content
   - Implement cache expiration (7 days)

3. **Error Handling**
   - Circuit breaker for repeated failures
   - Fallback to text-only response
   - Retry with exponential backoff

4. **Optimization**
   - Use eleven_flash_v2_5 for lowest latency
   - Optimize response text length
   - Stream audio for faster playback start

### Rate Limit Headers

```
X-RateLimit-Limit: 3
X-RateLimit-Remaining: 2
X-RateLimit-Reset: 1642262400
```

### Error Codes

- **429**: Rate limit exceeded - Wait and retry
- **401**: Invalid API key - Check credentials
- **400**: Invalid request - Check voice ID and model
- **503**: Service unavailable - Fallback to text

---

## Qdrant Cloud

### Service Details

**Website**: https://qdrant.io/  
**Status Page**: https://status.qdrant.io/  
**Documentation**: https://qdrant.tech/documentation/

### Configuration

**Collection**: Configured via application  
**Vector Dimension**: 384 (sentence-transformers)  
**Distance Metric**: Cosine similarity

### Rate Limits

**Free Tier**:
- Storage: 1GB
- Requests per second: 100
- Collections: Unlimited
- Vectors: ~1M (depending on payload size)

**Paid Tiers**:
- Storage: 1GB-100GB+
- Requests per second: Higher limits
- Dedicated clusters available

### Pricing

**Free Tier**: $0/month
- 1GB storage
- Shared cluster
- Community support

**Starter** (~$25/month):
- 4GB storage
- Dedicated resources
- Email support

**Production** (~$100+/month):
- Custom storage
- High availability
- Priority support

**Typical Usage**:
- Average memory: ~500 bytes per vector
- 1000 conversations: ~500KB
- Free tier sufficient for 1000+ users

### Best Practices

1. **Connection Management**
   - Use connection pooling/singleton pattern
   - Reuse client instances
   - Implement connection retry logic

2. **Query Optimization**
   - Limit top-K results (default: 3)
   - Use filters to narrow search space
   - Monitor query latency

3. **Data Management**
   - Implement memory pruning for old data
   - Archive inactive user memories
   - Monitor collection size

4. **Error Handling**
   - Circuit breaker for connection failures
   - Retry transient errors
   - Graceful degradation (continue without memory)

### Error Codes

- **429**: Rate limit exceeded - Implement backoff
- **503**: Service unavailable - Circuit breaker
- **401**: Invalid API key - Check credentials
- **404**: Collection not found - Initialize collection

---

## Together AI

### Service Details

**Website**: https://www.together.ai/  
**Documentation**: https://docs.together.ai/

**Note**: Image generation feature is currently frozen and not in active use.

### Model Used

**FLUX.1-schnell**:
- Purpose: Fast image generation
- Resolution: Up to 1024x1024
- Speed: ~3-5 seconds per image

### Rate Limits

**Free Tier**:
- Credits: $25 free credits
- Rate limits: Varies by model

**Paid Tier**:
- Pay-as-you-go pricing
- Higher rate limits

### Pricing

**FLUX.1-schnell**:
- ~$0.01-0.02 per image
- Varies by resolution and steps

**Typical Usage** (when enabled):
- Average: 1 image per 10 conversations
- Cost: ~$0.01 per image
- 1000 images: ~$10-20

### Best Practices

1. **Usage Management**
   - Only generate when explicitly requested
   - Implement request queuing
   - Cache generated images

2. **Error Handling**
   - Circuit breaker for failures
   - Graceful error messages
   - Retry with backoff

---

## Cost Estimation

### Monthly Cost Breakdown

**Low Usage** (100 conversations/month):
- Groq: ~$0.10
- ElevenLabs: Free tier (10K chars)
- Qdrant: Free tier
- **Total: ~$0.10/month**

**Medium Usage** (1,000 conversations/month):
- Groq: ~$1.00
- ElevenLabs: $5/month (Creator tier)
- Qdrant: Free tier
- **Total: ~$6/month**

**High Usage** (10,000 conversations/month):
- Groq: ~$10.00
- ElevenLabs: $22/month (Pro tier)
- Qdrant: Free tier (may need upgrade)
- **Total: ~$32/month**

**Very High Usage** (100,000 conversations/month):
- Groq: ~$100.00
- ElevenLabs: $99/month (Scale tier)
- Qdrant: ~$25/month (Starter tier)
- **Total: ~$224/month**

### Cost per Conversation

Average cost per conversation:
- Groq LLM: ~$0.001
- Groq STT: ~$0.002 (1 minute audio)
- ElevenLabs TTS: ~$0.06 (200 chars)
- Qdrant: Negligible
- **Total: ~$0.063 per conversation**

### Cost Optimization Strategies

1. **Reduce TTS Usage**
   - Implement aggressive caching
   - Shorten responses where appropriate
   - Consider alternative TTS providers

2. **Optimize LLM Usage**
   - Implement conversation summarization
   - Reduce context window size
   - Use smaller models for simple tasks

3. **Batch Operations**
   - Batch memory operations
   - Queue non-urgent requests
   - Implement request coalescing

---

## Monitoring and Optimization

### Key Metrics to Track

1. **API Usage**
   - Requests per minute/day
   - Token/character consumption
   - Cost per conversation

2. **Performance**
   - API latency by service
   - Error rates
   - Circuit breaker status

3. **Quotas**
   - Remaining quota percentage
   - Time until quota reset
   - Quota exhaustion alerts

### Monitoring Implementation

```python
# Example: Track API usage
import structlog

logger = structlog.get_logger()

def track_api_call(service: str, operation: str, duration_ms: int, cost: float):
    logger.info(
        "api_call",
        service=service,
        operation=operation,
        duration_ms=duration_ms,
        cost=cost
    )
```

### Alert Thresholds

**Groq**:
- Warning: > 80% of rate limit
- Critical: Rate limit exceeded

**ElevenLabs**:
- Warning: > 80% of monthly quota
- Critical: > 95% of monthly quota

**Qdrant**:
- Warning: > 80% of storage
- Critical: Connection failures

### Optimization Checklist

- [ ] Implement TTS response caching
- [ ] Monitor and optimize token usage
- [ ] Set up quota alerts
- [ ] Review and optimize prompt lengths
- [ ] Implement request batching where possible
- [ ] Monitor cost per conversation
- [ ] Set up budget alerts
- [ ] Review API usage patterns monthly

---

## Emergency Procedures

### Quota Exhaustion

**ElevenLabs Quota Exceeded**:
1. Switch to text-only responses
2. Notify users of temporary limitation
3. Upgrade plan or wait for quota reset
4. Implement stricter caching

**Groq Rate Limit Exceeded**:
1. Circuit breaker prevents further requests
2. Queue requests if possible
3. Notify users of temporary delay
4. Contact Groq for limit increase

### Service Outage

**Check Status Pages**:
- Groq: https://status.groq.com/
- ElevenLabs: https://status.elevenlabs.io/
- Qdrant: https://status.qdrant.io/

**Fallback Strategies**:
- Groq down: Return graceful error message
- ElevenLabs down: Text-only responses
- Qdrant down: Continue without memory context

---

## Related Documentation

- [Operations Runbook](OPERATIONS_RUNBOOK.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Monitoring and Observability](MONITORING_AND_OBSERVABILITY.md)
- [Security Documentation](SECURITY.md)

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2024-01-15 | 1.0 | Initial API limits documentation |

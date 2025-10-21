# External API Rate Limits and Quotas

## Overview

This document details the rate limits, quotas, and usage constraints for all external APIs used by the Rose the Healer Shaman application. Understanding these limits is critical for capacity planning, cost management, and incident response.

## Summary Table

| Service | Primary Use | Rate Limit | Monthly Quota | Cost Model |
|---------|-------------|------------|---------------|------------|
| Groq | LLM, STT | 30 req/min | Varies by plan | Per token |
| ElevenLabs | TTS | 50 req/min | 100K chars (free) | Per character |
| Qdrant Cloud | Vector DB | No hard limit | Storage-based | Per GB/month |
| Together AI | Image Gen | 600 req/min | Pay-as-you-go | Per image |

---

## Groq API

### Service Overview
- **Primary Use:** LLM inference, speech-to-text, vision
- **Models Used:**
  - `llama-3.3-70b-versatile` (primary LLM)
  - `gemma2-9b-it` (backup LLM)
  - `whisper-large-v3` (speech-to-text)
  - `llama-3.2-11b-vision-preview` (vision, frozen feature)

### Rate Limits

**Free Tier:**
- **Requests:** 30 requests per minute
- **Tokens:** 6,000 tokens per minute
- **Daily Limit:** 14,400 requests per day

**Paid Tier (Pay-as-you-go):**
- **Requests:** 30 requests per minute (same as free)
- **Tokens:** Higher limits based on model
- **Daily Limit:** No daily cap

**Per Model Limits:**
- `llama-3.3-70b`: 30 req/min, 6K tokens/min
- `gemma2-9b-it`: 30 req/min, 15K tokens/min
- `whisper-large-v3`: 20 req/min (audio transcription)

### Quotas and Costs

**Free Tier:**
- $25 free credits (limited time)
- No monthly quota after credits exhausted

**Paid Tier:**
- Pay per token
- `llama-3.3-70b`: ~$0.59 per 1M input tokens, ~$0.79 per 1M output tokens
- `whisper-large-v3`: ~$0.111 per hour of audio

### Usage Patterns

**Typical Request:**
- Voice message: 1 STT call + 1 LLM call = 2 requests
- Average tokens per conversation turn: 500-1000 tokens
- Average audio length: 10-30 seconds

**Capacity Estimate:**
- 30 req/min = 15 voice messages/min
- 900 voice messages/hour
- ~21,600 voice messages/day (free tier)

### Error Responses

**Rate Limit Exceeded (429):**
```json
{
  "error": {
    "message": "Rate limit exceeded",
    "type": "rate_limit_error",
    "code": "rate_limit_exceeded"
  }
}
```

**Quota Exceeded (429):**
```json
{
  "error": {
    "message": "You have exceeded your quota",
    "type": "insufficient_quota",
    "code": "insufficient_quota"
  }
}
```

### Mitigation Strategies

1. **Implement Exponential Backoff**
   - Current: 3 retries with exponential backoff
   - Wait times: 1s, 2s, 4s

2. **Circuit Breaker**
   - Open circuit after 5 consecutive failures
   - Recovery timeout: 60 seconds

3. **Request Queuing**
   - Queue requests when approaching limit
   - Process at sustainable rate

4. **Model Fallback**
   - Switch to `gemma2-9b-it` if `llama-3.3-70b` rate limited
   - Lower quality but higher throughput

### Monitoring

**Key Metrics:**
- Requests per minute
- Token usage per minute
- 429 error rate
- Average response time

**Alerts:**
- Warning: > 25 req/min (83% of limit)
- Critical: > 28 req/min (93% of limit)
- Error rate > 5%

---

## ElevenLabs API

### Service Overview
- **Primary Use:** Text-to-speech
- **Voice Used:** `eleven_flash_v2_5` (fast, low-latency)
- **Voice ID:** Configured via `ELEVENLABS_VOICE_ID`

### Rate Limits

**Free Tier:**
- **Requests:** 50 requests per minute
- **Concurrent:** 2 concurrent requests
- **Characters:** 10,000 characters per month

**Starter Tier ($5/month):**
- **Requests:** 50 requests per minute
- **Concurrent:** 3 concurrent requests
- **Characters:** 30,000 characters per month

**Creator Tier ($22/month):**
- **Requests:** 100 requests per minute
- **Concurrent:** 5 concurrent requests
- **Characters:** 100,000 characters per month

**Pro Tier ($99/month):**
- **Requests:** 200 requests per minute
- **Concurrent:** 10 concurrent requests
- **Characters:** 500,000 characters per month

### Quotas and Costs

**Character Limits:**
- Free: 10K chars/month (~100 responses)
- Starter: 30K chars/month (~300 responses)
- Creator: 100K chars/month (~1,000 responses)
- Pro: 500K chars/month (~5,000 responses)

**Overage Costs:**
- Additional characters: $0.30 per 1,000 characters

### Usage Patterns

**Typical Response:**
- Average response length: 100-200 characters
- Average audio duration: 10-20 seconds
- Characters per conversation: 200-400

**Capacity Estimate (Creator Tier):**
- 100K chars/month = ~1,000 responses
- ~33 responses/day
- Suitable for 10-20 active users

### Error Responses

**Rate Limit Exceeded (429):**
```json
{
  "detail": {
    "status": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Please try again later."
  }
}
```

**Quota Exceeded (429):**
```json
{
  "detail": {
    "status": "quota_exceeded",
    "message": "Character quota exceeded for this month."
  }
}
```

**Concurrent Limit (429):**
```json
{
  "detail": {
    "status": "concurrent_limit_exceeded",
    "message": "Too many concurrent requests."
  }
}
```

### Mitigation Strategies

1. **Response Caching**
   - Current: TTS caching implemented
   - Cache common responses
   - Reduce duplicate synthesis

2. **Response Length Optimization**
   - Keep responses concise
   - Target 100-150 characters
   - Avoid verbose responses

3. **Fallback to Text**
   - Return text-only if quota exceeded
   - Graceful degradation
   - Inform user of audio unavailability

4. **Concurrent Request Management**
   - Queue requests if at concurrent limit
   - Process sequentially if needed

### Monitoring

**Key Metrics:**
- Characters used per day
- Requests per minute
- Concurrent requests
- Cache hit rate

**Alerts:**
- Warning: > 80% monthly quota used
- Critical: > 95% monthly quota used
- Concurrent limit reached

---

## Qdrant Cloud

### Service Overview
- **Primary Use:** Vector database for long-term memory
- **Collection:** `rose_memories`
- **Vector Dimensions:** 384 (sentence-transformers)

### Rate Limits

**Free Tier:**
- **Storage:** 1 GB
- **Requests:** No hard rate limit
- **Vectors:** ~1M vectors (depending on metadata)

**Paid Tiers:**
- **Storage:** Pay per GB ($0.25/GB/month)
- **Requests:** No hard rate limit
- **Throughput:** Scales with cluster size

### Quotas and Costs

**Storage Costs:**
- $0.25 per GB per month
- Includes backups and replication

**Typical Usage:**
- Vector size: ~1.5 KB per memory
- 1 GB = ~650K memories
- Average user: 100-500 memories

**Capacity Estimate:**
- 1 GB supports 1,000-5,000 active users
- Growth rate: ~10 MB per 100 users per month

### Performance Characteristics

**Latency:**
- Search: 10-50ms (typical)
- Insert: 5-20ms (typical)
- Batch operations: More efficient

**Throughput:**
- Free tier: 100-500 req/sec
- Paid tier: 1,000+ req/sec

### Error Responses

**Storage Limit Exceeded:**
```json
{
  "status": "error",
  "message": "Storage limit exceeded"
}
```

**Connection Timeout:**
```json
{
  "status": "error",
  "message": "Connection timeout"
}
```

### Mitigation Strategies

1. **Connection Pooling**
   - Reuse client connections
   - Reduce connection overhead
   - Implement singleton pattern

2. **Batch Operations**
   - Batch inserts when possible
   - Reduce number of requests
   - Improve throughput

3. **Memory Cleanup**
   - Archive old memories
   - Delete inactive user data
   - Implement retention policy

4. **Circuit Breaker**
   - Fail fast on connection issues
   - Prevent cascading failures
   - Graceful degradation

### Monitoring

**Key Metrics:**
- Storage usage (GB)
- Request latency (p95)
- Error rate
- Collection size (vector count)

**Alerts:**
- Warning: > 80% storage used
- Critical: > 95% storage used
- Latency > 100ms (p95)

---

## Together AI (Frozen Feature)

### Service Overview
- **Primary Use:** Image generation (currently disabled)
- **Model:** `black-forest-labs/FLUX.1-schnell`
- **Status:** Feature frozen, not in production

### Rate Limits

**Free Tier:**
- **Requests:** 600 requests per minute
- **Images:** Pay-as-you-go

**Paid Tier:**
- **Requests:** 600 requests per minute
- **Images:** Pay-as-you-go

### Quotas and Costs

**Image Generation:**
- FLUX.1-schnell: ~$0.015 per image
- Average generation time: 3-5 seconds

**Capacity Estimate:**
- 600 req/min = 36,000 images/hour
- Cost: $540/hour at full capacity

### Usage Patterns (When Enabled)

**Typical Request:**
- 1 image per request
- Resolution: 1024x1024 (default)
- Generation time: 3-5 seconds

### Mitigation Strategies

1. **Feature Flag**
   - Currently disabled via `FEATURE_IMAGES=false`
   - Enable only when needed
   - Control via environment variable

2. **Rate Limiting**
   - Limit images per user per day
   - Implement cooldown period
   - Queue requests if needed

3. **Cost Controls**
   - Set daily budget limit
   - Alert on high usage
   - Disable if budget exceeded

---

## Capacity Planning

### Current Configuration (Free/Starter Tiers)

**Bottleneck:** ElevenLabs character quota

**Estimated Capacity:**
- **Daily Active Users:** 10-20
- **Conversations per Day:** 30-50
- **Voice Messages per Day:** 100-200

**Monthly Costs:**
- Groq: $0-10 (pay-as-you-go)
- ElevenLabs: $22 (Creator tier)
- Qdrant: $0-5 (< 1 GB)
- **Total: ~$30-40/month**

### Scaling to 100 Users

**Requirements:**
- Groq: Paid tier with higher limits
- ElevenLabs: Pro tier (500K chars)
- Qdrant: 2-5 GB storage

**Estimated Costs:**
- Groq: $50-100/month
- ElevenLabs: $99/month
- Qdrant: $1-2/month
- **Total: ~$150-200/month**

### Scaling to 1,000 Users

**Requirements:**
- Groq: Enterprise tier or multiple accounts
- ElevenLabs: Scale tier (custom pricing)
- Qdrant: 20-50 GB storage
- PostgreSQL for checkpointer

**Estimated Costs:**
- Groq: $500-1,000/month
- ElevenLabs: $500-1,000/month
- Qdrant: $5-15/month
- PostgreSQL: $25-50/month
- **Total: ~$1,000-2,000/month**

---

## Monitoring and Alerting

### Dashboard Metrics

**API Usage:**
- Requests per minute (by service)
- Error rate (by service)
- Response time (by service)
- Quota usage (% of limit)

**Cost Tracking:**
- Daily spend by service
- Monthly spend projection
- Cost per user
- Cost per conversation

### Alert Thresholds

**Rate Limits:**
- Warning: > 80% of rate limit
- Critical: > 95% of rate limit

**Quotas:**
- Warning: > 70% of monthly quota
- Critical: > 90% of monthly quota

**Costs:**
- Warning: > 80% of monthly budget
- Critical: > 100% of monthly budget

**Errors:**
- Warning: > 5% error rate
- Critical: > 10% error rate

---

## Emergency Procedures

### Quota Exhaustion

**Immediate Actions:**
1. Enable circuit breaker for affected service
2. Switch to fallback mode (text-only for TTS)
3. Notify users of degraded service
4. Upgrade plan or purchase additional quota

**Prevention:**
- Monitor quota usage daily
- Set alerts at 70% and 90%
- Plan upgrades before exhaustion

### Rate Limit Exceeded

**Immediate Actions:**
1. Enable request queuing
2. Implement exponential backoff
3. Switch to backup model if available
4. Scale horizontally if possible

**Prevention:**
- Monitor request rate
- Implement client-side rate limiting
- Use batch operations where possible

### Service Outage

**Immediate Actions:**
1. Check service status page
2. Enable circuit breaker
3. Return cached responses if available
4. Notify users of external service issue

**Prevention:**
- Implement circuit breakers
- Cache common responses
- Have fallback providers ready

---

## Related Documentation

- [Operations Runbook](OPERATIONS_RUNBOOK.md)
- [Incident Response Plan](INCIDENT_RESPONSE_PLAN.md)
- [Monitoring and Observability](MONITORING_AND_OBSERVABILITY.md)
- [Resource Management](RESOURCE_MANAGEMENT.md)

---

**Last Updated:** October 21, 2025  
**Next Review:** January 21, 2026  
**Owner:** Engineering Team

## References

- [Groq API Documentation](https://console.groq.com/docs)
- [ElevenLabs API Documentation](https://elevenlabs.io/docs/api-reference)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Together AI Documentation](https://docs.together.ai/)

# Frozen Interfaces

This directory contains interfaces that are implemented but not currently active in the main application.
They are preserved here for future activation when needed.

## Chainlit Interface (`chainlit/`)

A chat-based web interface using Chainlit. This was the original interface before the voice-first
React frontend was developed.

**Status:** Frozen - preserved for reference  
**Reason:** Replaced by voice-first React frontend

To activate:
1. Move `chainlit/` back to `../`
2. Install chainlit dependency (already in pyproject.toml)
3. Run: `chainlit run src/ai_companion/interfaces/chainlit/app.py`

## WhatsApp Interface (`whatsapp/`)

Webhook-based WhatsApp integration for receiving and responding to messages.

**Status:** Frozen - ready for future activation  
**Reason:** Planned for future release

To activate:
1. Move `whatsapp/` back to `../`
2. Configure WhatsApp Business API credentials
3. Set up webhook endpoints
4. See documentation in `docs/` for setup details

from fastapi import FastAPI

app = FastAPI()

# ============================================================================
# WhatsApp Integration - FROZEN FOR FUTURE RELEASE
# ============================================================================
# The WhatsApp integration has been disabled for the initial Rose release
# to focus on the voice-first web interface. All WhatsApp code is preserved
# for future activation when multi-channel support is needed.
#
# To re-enable WhatsApp:
# 1. Uncomment the line below
# 2. Ensure WHATSAPP_* environment variables are set in settings.py
# 3. Configure WhatsApp webhook in Meta Developer Console
# ============================================================================
# app.include_router(whatsapp_router)

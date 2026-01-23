"""
Webhooks module for handling Vapi call events.
"""

from .server import app, WebhookEvent

__all__ = ["app", "WebhookEvent"]

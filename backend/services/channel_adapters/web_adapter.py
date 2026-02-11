"""
LK Clinic Tools - Web Widget Channel Adapter
Handles WebSocket communication for the embeddable website chat widget.
"""

from typing import Any, Optional

from services.channel_adapters.base import (
    ChannelAdapter,
    InboundMessage,
    OutboundMessage,
)


# In-memory connection store (for production, use Redis pub/sub)
_active_connections: dict[str, Any] = {}


class WebAdapter(ChannelAdapter):
    """WebSocket-based adapter for the website chat widget."""

    def __init__(self, clinic_id: str, bot_id: str):
        self.clinic_id = clinic_id
        self.bot_id = bot_id

    async def send_message(self, message: OutboundMessage) -> dict:
        """Send a message to the web widget via WebSocket."""
        ws = _active_connections.get(message.to)
        if not ws:
            return {"status": "disconnected", "session_id": message.to}

        payload = {
            "type": "bot_message",
            "text": message.text,
            "buttons": message.buttons,
            "list_items": message.list_items,
            "image_url": message.image_url,
            "image_caption": message.image_caption,
        }

        await ws.send_json(payload)
        return {"status": "sent", "session_id": message.to}

    async def parse_webhook(self, payload: dict) -> Optional[InboundMessage]:
        """Parse incoming WebSocket message into InboundMessage."""
        msg_type = payload.get("type", "text")

        if msg_type == "button_click":
            return InboundMessage(
                sender=payload.get("session_id", ""),
                button_id=payload.get("button_id"),
                text=payload.get("button_text"),
                message_type="button_response",
                raw_payload=payload,
            )

        if msg_type == "list_select":
            return InboundMessage(
                sender=payload.get("session_id", ""),
                list_item_id=payload.get("item_id"),
                text=payload.get("item_text"),
                message_type="list_response",
                raw_payload=payload,
            )

        return InboundMessage(
            sender=payload.get("session_id", ""),
            text=payload.get("text", ""),
            message_type="text",
            raw_payload=payload,
        )

    async def send_text(self, to: str, text: str) -> dict:
        """Send a plain text message to the widget."""
        return await self.send_message(OutboundMessage(to=to, text=text))

    async def send_buttons(
        self, to: str, text: str, buttons: list[dict[str, str]]
    ) -> dict:
        """Send a message with buttons to the widget."""
        return await self.send_message(
            OutboundMessage(to=to, text=text, buttons=buttons)
        )

    async def send_list(
        self,
        to: str,
        text: str,
        button_text: str,
        items: list[dict[str, str]],
    ) -> dict:
        """Send a list menu to the widget."""
        return await self.send_message(
            OutboundMessage(to=to, text=text, list_items=items, list_title=button_text)
        )


def register_connection(session_id: str, websocket: Any):
    """Register a WebSocket connection for a chat session."""
    _active_connections[session_id] = websocket


def unregister_connection(session_id: str):
    """Remove a WebSocket connection when disconnected."""
    _active_connections.pop(session_id, None)

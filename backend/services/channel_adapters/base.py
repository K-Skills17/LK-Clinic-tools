"""
LK Clinic Tools - Channel Adapter Base
Abstract base class for messaging channel adapters (WhatsApp, Web Widget).
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from pydantic import BaseModel


class OutboundMessage(BaseModel):
    """Standardized outbound message format."""
    to: str  # phone number or session id
    text: Optional[str] = None
    image_url: Optional[str] = None
    image_caption: Optional[str] = None
    document_url: Optional[str] = None
    document_caption: Optional[str] = None
    buttons: Optional[list[dict[str, str]]] = None  # [{id, title}], max 3
    list_items: Optional[list[dict[str, str]]] = None  # [{id, title, description}], max 10
    list_title: Optional[str] = None


class InboundMessage(BaseModel):
    """Standardized inbound message format."""
    sender: str  # phone number or session id
    text: Optional[str] = None
    button_id: Optional[str] = None  # if user clicked a button
    list_item_id: Optional[str] = None  # if user selected a list item
    message_type: str = "text"  # text, button_response, list_response, image, audio
    raw_payload: Optional[dict[str, Any]] = None


class ChannelAdapter(ABC):
    """
    Abstract base for messaging channel adapters.
    Implementations: WhatsApp (Evolution API), Web Widget (WebSocket).
    """

    @abstractmethod
    async def send_message(self, message: OutboundMessage) -> dict:
        """Send a message through this channel. Returns delivery info."""
        ...

    @abstractmethod
    async def parse_webhook(self, payload: dict) -> Optional[InboundMessage]:
        """Parse an incoming webhook/event into standardized InboundMessage."""
        ...

    @abstractmethod
    async def send_text(self, to: str, text: str) -> dict:
        """Convenience: send a plain text message."""
        ...

    @abstractmethod
    async def send_buttons(
        self, to: str, text: str, buttons: list[dict[str, str]]
    ) -> dict:
        """Convenience: send a message with buttons (max 3)."""
        ...

    @abstractmethod
    async def send_list(
        self,
        to: str,
        text: str,
        button_text: str,
        items: list[dict[str, str]],
    ) -> dict:
        """Convenience: send a message with a list menu (max 10 items)."""
        ...

"""
LK Clinic Tools - WhatsApp Channel Adapter
Communicates with Evolution API for WhatsApp messaging.
"""

from typing import Any, Optional

import httpx

from services.channel_adapters.base import (
    ChannelAdapter,
    InboundMessage,
    OutboundMessage,
)


class WhatsAppAdapter(ChannelAdapter):
    """Evolution API adapter for WhatsApp messaging."""

    def __init__(self, api_url: str, api_key: str, instance_name: str):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.instance_name = instance_name
        self.headers = {"apikey": api_key, "Content-Type": "application/json"}

    def _url(self, path: str) -> str:
        return f"{self.api_url}/message/{path}/{self.instance_name}"

    async def send_message(self, message: OutboundMessage) -> dict:
        """Send a message through WhatsApp via Evolution API."""
        if message.buttons:
            return await self.send_buttons(message.to, message.text or "", message.buttons)
        if message.list_items:
            return await self.send_list(
                message.to,
                message.text or "",
                message.list_title or "Opções",
                message.list_items,
            )
        if message.image_url:
            return await self._send_media(message.to, "image", message.image_url, message.image_caption)
        if message.document_url:
            return await self._send_media(message.to, "document", message.document_url, message.document_caption)
        return await self.send_text(message.to, message.text or "")

    async def parse_webhook(self, payload: dict) -> Optional[InboundMessage]:
        """Parse Evolution API webhook payload into InboundMessage."""
        data = payload.get("data", {})
        key = data.get("key", {})
        message_data = data.get("message", {})

        if key.get("fromMe"):
            return None  # Ignore own messages

        sender = key.get("remoteJid", "").replace("@s.whatsapp.net", "")
        if not sender:
            return None

        # Button response
        if "buttonsResponseMessage" in message_data:
            return InboundMessage(
                sender=sender,
                button_id=message_data["buttonsResponseMessage"].get("selectedButtonId"),
                text=message_data["buttonsResponseMessage"].get("selectedDisplayText"),
                message_type="button_response",
                raw_payload=payload,
            )

        # List response
        if "listResponseMessage" in message_data:
            return InboundMessage(
                sender=sender,
                list_item_id=message_data["listResponseMessage"].get("singleSelectReply", {}).get("selectedRowId"),
                text=message_data["listResponseMessage"].get("title"),
                message_type="list_response",
                raw_payload=payload,
            )

        # Regular text
        text = (
            message_data.get("conversation")
            or message_data.get("extendedTextMessage", {}).get("text")
            or ""
        )

        return InboundMessage(
            sender=sender,
            text=text,
            message_type="text",
            raw_payload=payload,
        )

    async def send_text(self, to: str, text: str) -> dict:
        """Send a plain text message."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._url("sendText"),
                headers=self.headers,
                json={"number": to, "text": text},
            )
            return response.json()

    async def send_buttons(
        self, to: str, text: str, buttons: list[dict[str, str]]
    ) -> dict:
        """Send a message with buttons (max 3 for WhatsApp)."""
        button_payload = [
            {"buttonId": btn["id"], "buttonText": {"displayText": btn["title"]}}
            for btn in buttons[:3]  # WhatsApp limit: 3 buttons
        ]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._url("sendButtons"),
                headers=self.headers,
                json={
                    "number": to,
                    "title": "",
                    "description": text,
                    "buttons": button_payload,
                },
            )
            return response.json()

    async def send_list(
        self,
        to: str,
        text: str,
        button_text: str,
        items: list[dict[str, str]],
    ) -> dict:
        """Send a list menu message (max 10 items for WhatsApp)."""
        rows = [
            {
                "rowId": item["id"],
                "title": item["title"],
                "description": item.get("description", ""),
            }
            for item in items[:10]  # WhatsApp limit: 10 items
        ]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._url("sendList"),
                headers=self.headers,
                json={
                    "number": to,
                    "title": "",
                    "description": text,
                    "buttonText": button_text,
                    "sections": [{"title": "Opções", "rows": rows}],
                },
            )
            return response.json()

    async def _send_media(
        self, to: str, media_type: str, url: str, caption: Optional[str] = None
    ) -> dict:
        """Send media (image, document, audio)."""
        endpoint = {
            "image": "sendMedia",
            "document": "sendMedia",
            "audio": "sendWhatsAppAudio",
        }.get(media_type, "sendMedia")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._url(endpoint),
                headers=self.headers,
                json={
                    "number": to,
                    "mediatype": media_type,
                    "media": url,
                    "caption": caption or "",
                },
            )
            return response.json()

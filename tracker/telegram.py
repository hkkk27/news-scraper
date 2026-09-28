"""Minimal Telegram Bot API client (HTTPS calls only; no framework needed)."""

from __future__ import annotations

import json
from typing import Any

import httpx

API = "https://api.telegram.org"


class TelegramError(RuntimeError):
    pass


class TelegramClient:
    def __init__(self, token: str, timeout: float = 30):
        if not token:
            raise TelegramError("TELEGRAM_BOT_TOKEN is not set")
        self._base = f"{API}/bot{token}"
        self._file_base = f"{API}/file/bot{token}"
        self._http = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._http.close()

    def call(self, method: str, **params: Any) -> Any:
        payload = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in params.items() if v is not None}
        response = self._http.post(f"{self._base}/{method}", data=payload)
        data = response.json()
        if not data.get("ok"):
            raise TelegramError(f"{method}: {data.get('description', response.status_code)}")
        return data["result"]

    # --- methods used by the bot -------------------------------------------------------------

    def get_updates(self, offset: int | None = None, timeout: int = 0) -> list[dict]:
        return self.call("getUpdates", offset=offset, timeout=timeout,
                         allowed_updates=["message", "callback_query"])

    def send_message(self, chat_id: int, text: str, reply_markup: dict | None = None,
                     disable_preview: bool = True) -> dict:
        return self.call("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML",
                         reply_markup=reply_markup, disable_web_page_preview=disable_preview)

    def answer_callback(self, callback_id: str, text: str = "") -> None:
        self.call("answerCallbackQuery", callback_query_id=callback_id, text=text)

    def edit_reply_markup(self, chat_id: int, message_id: int, reply_markup: dict) -> None:
        self.call("editMessageReplyMarkup", chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)

    def download_file(self, file_id: str, max_bytes: int = 15 * 1024 * 1024) -> bytes:
        info = self.call("getFile", file_id=file_id)
        if info.get("file_size", 0) > max_bytes:
            raise TelegramError("file too large")
        response = self._http.get(f"{self._file_base}/{info['file_path']}")
        response.raise_for_status()
        return response.content

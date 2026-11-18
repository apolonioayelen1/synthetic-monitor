import logging
from dataclasses import dataclass
from pathlib import Path

import requests

from src.core.config import Settings


@dataclass(slots=True)
class AlertPayload:
    title: str
    layer: str
    step_name: str
    duration_seconds: float
    sla_threshold_seconds: float
    url: str
    error_trace: str
    summary: str
    screenshot_path: Path | None = None
    trace_path: Path | None = None


class AlertManager:
    """Dispatches synthetic failure/SLA alerts to Telegram and/or Slack."""

    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger

    def send_failure_alert(self, payload: AlertPayload) -> None:
        message = self._format_message(payload)

        if not self.settings.telegram_enabled and not self.settings.slack_enabled:
            self.logger.warning(
                "Alerting disabled (no TELEGRAM_* or SLACK_WEBHOOK_URL configured)."
            )
            return

        if self.settings.telegram_enabled:
            self._send_telegram(message, payload.screenshot_path)

        if self.settings.slack_enabled:
            self._send_slack(message)

    def _format_message(self, payload: AlertPayload) -> str:
        trace_info = str(payload.trace_path) if payload.trace_path else "N/A"
        short_error = payload.error_trace.strip()[-400:]
        return (
            f"🚨 {payload.title}\n"
            f"Layer: {payload.layer}\n"
            f"Step: {payload.step_name}\n"
            f"Duration: {payload.duration_seconds:.3f}s (SLA: {payload.sla_threshold_seconds:.1f}s)\n"
            f"URL: {payload.url or 'N/A'}\n"
            f"Trace: {trace_info}\n\n"
            f"Metrics:\n{payload.summary}\n\n"
            f"Error:\n{short_error}"
        )

    def _send_telegram(self, message: str, screenshot_path: Path | None) -> None:
        base_api = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}"
        try:
            if screenshot_path and screenshot_path.exists():
                with screenshot_path.open("rb") as photo_file:
                    resp = requests.post(
                        f"{base_api}/sendPhoto",
                        data={
                            "chat_id": self.settings.telegram_chat_id,
                            "caption": message[:1000],
                        },
                        files={"photo": photo_file},
                        timeout=15,
                    )
            else:
                resp = requests.post(
                    f"{base_api}/sendMessage",
                    json={
                        "chat_id": self.settings.telegram_chat_id,
                        "text": message[:4000],
                    },
                    timeout=15,
                )
            resp.raise_for_status()
            self.logger.info("Telegram alert dispatched successfully.")
        except requests.RequestException as exc:
            self.logger.error(f"Failed to send Telegram alert: {exc}")

    def _send_slack(self, message: str) -> None:
        try:
            resp = requests.post(
                self.settings.slack_webhook_url,
                json={"text": message[:3500]},
                timeout=15,
            )
            resp.raise_for_status()
            self.logger.info("Slack alert dispatched successfully.")
        except requests.RequestException as exc:
            self.logger.error(f"Failed to send Slack alert: {exc}")
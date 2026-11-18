import logging
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from src.core.config import Settings, get_settings
from src.observability.alerter import AlertManager, AlertPayload
from src.observability.logger import get_logger
from src.observability.metrics import MetricsCollector


class BrowserSessionManager:
    """Manages lazy browser startup, tracing, and failure artifact capture."""

    def __init__(
        self,
        playwright: Playwright,
        settings: Settings,
        logger: logging.Logger,
    ) -> None:
        self._playwright = playwright
        self._settings = settings
        self._logger = logger
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    def start(self) -> Page:
        """Launch Chromium with fixed viewport and start Playwright tracing."""
        self._logger.info(
            f"Launching Chromium (headless={self._settings.browser_headless}, "
            f"viewport={self._settings.viewport_width}x{self._settings.viewport_height})"
        )
        self._browser = self._playwright.chromium.launch(
            headless=self._settings.browser_headless,
            args=["--disable-dev-shm-usage"],
        )
        self._context = self._browser.new_context(
            viewport={
                "width": self._settings.viewport_width,
                "height": self._settings.viewport_height,
            }
        )
        self._context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self._page = self._context.new_page()
        return self._page

    def teardown(
        self,
        failed: bool,
        error_trace: str,
        collector: MetricsCollector,
        alerter: AlertManager,
    ) -> None:
        """Capture screenshot + trace on failure, dispatch alert, and close browser."""
        screenshot_path: Path | None = None
        trace_path: Path | None = None
        artifacts_dir = self._settings.ensure_artifacts_dir()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

        if failed:
            if self._page is not None:
                try:
                    screenshot_path = artifacts_dir / f"failure_{stamp}.png"
                    self._page.screenshot(path=str(screenshot_path), full_page=True)
                    self._logger.info(f"Saved failure screenshot: {screenshot_path}")
                except Exception as exc:
                    self._logger.warning(f"Could not capture screenshot: {exc}")
                    screenshot_path = None

            if self._context is not None:
                try:
                    trace_path = artifacts_dir / f"trace_{stamp}.zip"
                    self._context.tracing.stop(path=str(trace_path))
                    self._logger.info(f"Saved Playwright trace: {trace_path}")
                except Exception as exc:
                    self._logger.warning(f"Could not save Playwright trace: {exc}")
                    trace_path = None

            failed_step = collector.failed_steps[-1] if collector.failed_steps else None
            current_url = ""
            if failed_step and failed_step.url:
                current_url = failed_step.url
            elif self._page is not None:
                try:
                    current_url = self._page.url
                except Exception:
                    current_url = ""

            payload = AlertPayload(
                title="Synthetic Monitor Failure / SLA Breach",
                layer=failed_step.layer if failed_step else "UNKNOWN",
                step_name=failed_step.name if failed_step else "test_execution",
                duration_seconds=failed_step.duration_seconds if failed_step else 0.0,
                sla_threshold_seconds=self._settings.sla_threshold_seconds,
                url=current_url,
                error_trace=(failed_step.error if failed_step and failed_step.error else error_trace),
                summary=collector.format_summary() or "No step metrics recorded.",
                screenshot_path=screenshot_path,
                trace_path=trace_path,
            )
            alerter.send_failure_alert(payload)
        elif self._context is not None:
            try:
                self._context.tracing.stop()
            except Exception:
                pass

        if self._context is not None:
            self._context.close()
        if self._browser is not None:
            self._browser.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]) -> Iterator[None]:
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(scope="session")
def settings() -> Settings:
    return get_settings()


@pytest.fixture(scope="session")
def logger(settings: Settings) -> logging.Logger:
    return get_logger(log_dir=settings.ensure_artifacts_dir())


@pytest.fixture
def metrics_collector() -> MetricsCollector:
    return MetricsCollector()


@pytest.fixture(scope="session")
def alert_manager(settings: Settings, logger: logging.Logger) -> AlertManager:
    return AlertManager(settings=settings, logger=logger)


@pytest.fixture(scope="session")
def pw_instance() -> Iterator[Playwright]:
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture
def browser_session(
    request: pytest.FixtureRequest,
    pw_instance: Playwright,
    settings: Settings,
    logger: logging.Logger,
    metrics_collector: MetricsCollector,
    alert_manager: AlertManager,
) -> Iterator[BrowserSessionManager]:
    manager = BrowserSessionManager(
        playwright=pw_instance,
        settings=settings,
        logger=logger,
    )
    yield manager

    rep_call = getattr(request.node, "rep_call", None)
    rep_setup = getattr(request.node, "rep_setup", None)
    failed = bool((rep_call and rep_call.failed) or (rep_setup and rep_setup.failed))
    error_trace = ""
    if rep_call and rep_call.failed:
        error_trace = str(rep_call.longrepr)
    elif rep_setup and rep_setup.failed:
        error_trace = str(rep_setup.longrepr)

    manager.teardown(
        failed=failed,
        error_trace=error_trace,
        collector=metrics_collector,
        alerter=alert_manager,
    )
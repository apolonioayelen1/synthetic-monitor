import logging

from playwright.sync_api import APIRequestContext, Playwright

from src.core.sla_timer import measure_step
from src.observability.metrics import MetricsCollector


def check_api_health(
    playwright: Playwright,
    url: str,
    sla_threshold_seconds: float,
    collector: MetricsCollector,
    logger: logging.Logger,
) -> None:
    """Verify endpoint availability and latency via Playwright APIRequestContext before browser launch."""
    request_context: APIRequestContext = playwright.request.new_context()
    timeout_ms = int((sla_threshold_seconds + 2.0) * 1000)

    try:
        with measure_step(
            name="api_health_check",
            layer="API",
            sla_threshold_seconds=sla_threshold_seconds,
            collector=collector,
            logger=logger,
            url_provider=lambda: url,
        ):
            response = request_context.get(url, timeout=timeout_ms)
            assert response.ok, f"API health check failed: HTTP {response.status} on {url}"
            body = response.body()
            assert len(body) > 0, f"API health check returned empty body on {url}"
    finally:
        request_context.dispose()
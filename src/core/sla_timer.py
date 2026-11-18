import logging
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager

from src.observability.metrics import MetricsCollector, StepLayer, StepMetric


class SLABreachError(AssertionError):
    """Raised when a synthetic step exceeds its configured SLA latency threshold."""


def _safe_url(url_provider: Callable[[], str] | None) -> str:
    if url_provider is None:
        return ""
    try:
        return url_provider()
    except Exception:
        return ""


@contextmanager
def measure_step(
    name: str,
    layer: StepLayer,
    sla_threshold_seconds: float,
    collector: MetricsCollector,
    logger: logging.Logger,
    url_provider: Callable[[], str] | None = None,
) -> Iterator[None]:
    """Measure pure step duration and enforce SLA threshold."""
    start = time.perf_counter()
    error_message = ""
    passed = True

    try:
        yield
    except Exception as exc:
        passed = False
        error_message = f"{type(exc).__name__}: {exc}"
        duration = time.perf_counter() - start
        sla_breached = duration > sla_threshold_seconds
        current_url = _safe_url(url_provider)

        collector.record(
            StepMetric(
                name=name,
                layer=layer,
                duration_seconds=duration,
                sla_threshold_seconds=sla_threshold_seconds,
                passed=False,
                sla_breached=sla_breached,
                url=current_url,
                error=error_message,
            )
        )
        logger.error(
            f"[{layer}] {name} FAILED in {duration:.3f}s | URL={current_url} | {error_message}"
        )
        raise

    duration = time.perf_counter() - start
    sla_breached = duration > sla_threshold_seconds
    current_url = _safe_url(url_provider)

    if sla_breached:
        error_message = (
            f"SLA breach on '{name}' ({layer}): {duration:.3f}s > {sla_threshold_seconds:.2f}s"
        )

    collector.record(
        StepMetric(
            name=name,
            layer=layer,
            duration_seconds=duration,
            sla_threshold_seconds=sla_threshold_seconds,
            passed=passed,
            sla_breached=sla_breached,
            url=current_url,
            error=error_message,
        )
    )

    if sla_breached:
        logger.error(f"[{layer}] {error_message} | URL={current_url}")
        raise SLABreachError(error_message)

    logger.info(
        f"[{layer}] {name} passed in {duration:.3f}s (SLA <= {sla_threshold_seconds:.2f}s)"
    )
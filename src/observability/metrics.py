from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

StepLayer = Literal["API", "UI"]


@dataclass(slots=True)
class StepMetric:
    name: str
    layer: StepLayer
    duration_seconds: float
    sla_threshold_seconds: float
    passed: bool
    sla_breached: bool
    url: str = ""
    error: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    )

    def to_dict(self) -> dict[str, str | float | bool]:
        return {
            "name": self.name,
            "layer": self.layer,
            "duration_seconds": round(self.duration_seconds, 3),
            "sla_threshold_seconds": self.sla_threshold_seconds,
            "passed": self.passed,
            "sla_breached": self.sla_breached,
            "url": self.url,
            "error": self.error,
            "timestamp": self.timestamp,
        }


class MetricsCollector:
    """Collects per-step execution metrics for the synthetic run."""

    def __init__(self) -> None:
        self.steps: list[StepMetric] = []

    def record(self, metric: StepMetric) -> None:
        self.steps.append(metric)

    @property
    def failed_steps(self) -> list[StepMetric]:
        return [s for s in self.steps if not s.passed or s.sla_breached]

    def format_summary(self) -> str:
        lines: list[str] = []
        for step in self.steps:
            status = "PASS" if (step.passed and not step.sla_breached) else "FAIL"
            sla_tag = " [SLA BREACH]" if step.sla_breached else ""
            lines.append(
                f"[{status}{sla_tag}] ({step.layer}) {step.name}: "
                f"{step.duration_seconds:.3f}s / {step.sla_threshold_seconds:.1f}s"
            )
        return "\n".join(lines)
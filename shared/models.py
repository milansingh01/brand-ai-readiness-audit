from dataclasses import dataclass, asdict
from typing import Any, Optional


@dataclass
class Observation:
    """
    Raw deterministic result produced by an audit script.

    The script should report what it observed.
    It should NOT decide severity or suggested action.
    """

    check: str
    found: bool
    evidence: Any
    details: Optional[dict] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class Finding:
    """
    Interpreted finding used in the final audit report.

    Severity, title and suggested action are assigned
    by the audit agent/orchestrator.
    """

    id: str
    title: str
    severity: str
    evidence: str
    suggested_action: str
    priority: Optional[int] = None
    priority_reason: Optional[str] = None

    def to_dict(self):
        return asdict(self)
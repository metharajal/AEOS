"""
AEOS Memory Layer — local-first diagnostic memory.

Stores structured snapshots of AEOS audit results locally.
No network access. No secrets. No AI inference.
"""

from aeos.memory.compare import (
    MemoryCompareDelta,
    MemoryCompareResult,
    compare_records,
    compute_trend,
    load_record_reference,
)
from aeos.memory.models import MemoryListResult, MemoryRecord, MemoryRecordSummary
from aeos.memory.store import (
    build_memory_record_from_reclaim_harden,
    find_record_path,
    list_records,
    load_record,
    save_record,
)
from aeos.memory.timeline import (
    MemoryTimelineEntry,
    MemoryTimelineResult,
    MemoryTimelineSynthesis,
    build_timeline,
    compute_timeline_synthesis,
    load_project_records,
    timeline_to_dict,
)

__all__ = [
    "MemoryCompareDelta",
    "MemoryCompareResult",
    "MemoryListResult",
    "MemoryRecord",
    "MemoryRecordSummary",
    "MemoryTimelineEntry",
    "MemoryTimelineResult",
    "MemoryTimelineSynthesis",
    "build_memory_record_from_reclaim_harden",
    "build_timeline",
    "compare_records",
    "compute_timeline_synthesis",
    "compute_trend",
    "find_record_path",
    "list_records",
    "load_project_records",
    "load_record",
    "load_record_reference",
    "save_record",
    "timeline_to_dict",
]

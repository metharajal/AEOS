"""
AEOS Build Rail — plan and scaffold AEOS-native projects.

No network access. No AI inference. No secrets.
"""

from aeos.build.planner import (
    VALID_STACKS,
    VALID_TYPES,
    BuildPlan,
    build_plan_to_dict,
    create_build_plan,
    validate_project_type,
    validate_stack,
)
from aeos.build.scaffold import (
    BuildScaffoldResult,
    ScaffoldedFile,
    ensure_safe_output_directory,
    render_scaffold_files,
    scaffold_build_project,
    scaffold_result_to_dict,
)

__all__ = [
    "VALID_STACKS",
    "VALID_TYPES",
    "BuildPlan",
    "BuildScaffoldResult",
    "ScaffoldedFile",
    "build_plan_to_dict",
    "create_build_plan",
    "ensure_safe_output_directory",
    "render_scaffold_files",
    "scaffold_build_project",
    "scaffold_result_to_dict",
    "validate_project_type",
    "validate_stack",
]

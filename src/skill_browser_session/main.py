from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any


def _is_core_repo(candidate: Path) -> bool:
    return candidate.is_dir() and (candidate / "pyproject.toml").is_file() and (candidate / "ecosystem").is_dir()


def _candidate_core_repos() -> list[Path]:
    current_file = Path(__file__).resolve()
    repo_root = current_file.parents[2]
    candidates: list[Path] = []

    configured = str(os.getenv("AUTOBOT_CORE_REPO", "")).strip()
    if configured:
        candidates.append(Path(configured).expanduser())

    for anchor in (current_file.parent, Path.cwd().resolve()):
        candidates.extend([anchor, *anchor.parents])

    parent_dir = repo_root.parent
    if parent_dir.exists():
        candidates.extend(path for path in parent_dir.iterdir() if path.is_dir())

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        key = str(resolved).lower()
        if key not in seen:
            seen.add(key)
            unique.append(resolved)
    return unique


def _default_core_repo() -> Path:
    for candidate in _candidate_core_repos():
        if _is_core_repo(candidate):
            return candidate
    raise RuntimeError("Unable to locate the core repo. Set AUTOBOT_CORE_REPO to a valid core repo path.")


def _ensure_core_repo_on_path() -> Path:
    candidate = _default_core_repo()
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
    return candidate


_CORE_REPO = _ensure_core_repo_on_path()

from ecosystem.contracts import HealthSnapshot, TaskRequest, TaskResult  # noqa: E402
from ecosystem.skills import BaseSkill, SkillCapability, SkillManifest  # noqa: E402

if TYPE_CHECKING:
    from ecosystem.domains.desktop_control.browser_session_tool_adapter import BrowserSessionToolAdapter


def _map_status(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"completed", "success", "ok"}:
        return "completed"
    if normalized in {"blocked", "needs_confirmation", "awaiting_confirmation"}:
        return "blocked"
    if normalized in {"preview", "dry_run"}:
        return "preview"
    return "failed"


_CAPABILITY_TO_ACTION = {
    "browser_session.observe_page": "observe_page",
    "browser_session.type_text": "type_text",
    "browser_session.click_text": "click_text",
    "browser_session.fill_field": "fill_field",
    "browser_session.fill_form": "fill_form",
    "browser_session.follow_link": "follow_link",
}


class Skill(BaseSkill):
    def __init__(self, adapter: "BrowserSessionToolAdapter" | None = None) -> None:
        self._adapter = adapter

    @property
    def adapter(self) -> "BrowserSessionToolAdapter":
        if self._adapter is None:
            from ecosystem.config import get_settings
            from ecosystem.domains.desktop_control.browser_session_tool_adapter import BrowserSessionToolAdapter

            settings = get_settings()
            self._adapter = BrowserSessionToolAdapter(
                outputs_dir=settings.outputs_dir,
                state_dir=settings.state_dir,
            )
        return self._adapter

    def manifest(self) -> SkillManifest:
        return SkillManifest(
            name="skill-browser-session",
            version="0.1.0",
            mode="local_plugin",
            entrypoint="src.skill_browser_session.main:Skill",
            core_api=">=1.0,<2.0",
            capabilities=[
                SkillCapability(
                    id="browser_session.observe_page",
                    description="Observe the current browser page or a target URL.",
                    input_schema={"type": "object"},
                    output_schema={"type": "object"},
                    observability_events=["browser_session.observe_page"],
                    retry_policy="bounded_backoff",
                ),
                SkillCapability(
                    id="browser_session.type_text",
                    description="Type text into the active browser window.",
                    input_schema={"type": "object"},
                    output_schema={"type": "object"},
                    risk_level="medium",
                    confirmation_required=True,
                    retry_policy="manual_review",
                    observability_events=["browser_session.type_text"],
                ),
                SkillCapability(
                    id="browser_session.click_text",
                    description="Click a visible control or text in the browser.",
                    input_schema={"type": "object"},
                    output_schema={"type": "object"},
                    risk_level="medium",
                    confirmation_required=True,
                    retry_policy="manual_review",
                    observability_events=["browser_session.click_text"],
                ),
                SkillCapability(
                    id="browser_session.fill_field",
                    description="Fill a visible field in the browser.",
                    input_schema={"type": "object"},
                    output_schema={"type": "object"},
                    risk_level="medium",
                    confirmation_required=True,
                    retry_policy="manual_review",
                    observability_events=["browser_session.fill_field"],
                ),
                SkillCapability(
                    id="browser_session.fill_form",
                    description="Fill a structured browser form.",
                    input_schema={"type": "object"},
                    output_schema={"type": "object"},
                    risk_level="medium",
                    confirmation_required=True,
                    retry_policy="manual_review",
                    observability_events=["browser_session.fill_form"],
                ),
                SkillCapability(
                    id="browser_session.follow_link",
                    description="Follow a visible browser link.",
                    input_schema={"type": "object"},
                    output_schema={"type": "object"},
                    risk_level="medium",
                    confirmation_required=True,
                    retry_policy="manual_review",
                    observability_events=["browser_session.follow_link"],
                ),
            ],
            permissions={
                "read_memory": False,
                "write_memory": False,
                "internet_access": True,
                "file_write": False,
                "external_actions": True,
            },
            healthcheck={"kind": "python", "target": "src.skill_browser_session.main:healthcheck"},
            timeout_ms=120000,
            enabled_by_default=True,
        )

    def healthcheck(self) -> HealthSnapshot:
        return HealthSnapshot(
            status="healthy",
            available=True,
            updated_at=None,
            detail="Browser session adapter is available.",
            counters={},
            evidence={"bridge_mode": True},
        )

    def execute(self, request: TaskRequest) -> TaskResult:
        capability = str(request.capability or "").strip()
        if capability not in _CAPABILITY_TO_ACTION:
            raise ValueError(f"Unsupported capability: {capability}")
        params = dict(request.parameters or {})
        from ecosystem.domains.desktop_control.software_tool_models import ToolActionRequest

        tool_request = ToolActionRequest(
            adapter_name="browser_session",
            action=_CAPABILITY_TO_ACTION[capability],
            target=params.pop("target", None),
            parameters=params,
            dry_run=bool((request.parameters or {}).get("dry_run", False)),
            confirmed=bool((request.parameters or {}).get("confirmed", False)),
            confirmation_token=(request.parameters or {}).get("confirmation_token"),
            policy_approved=bool((request.parameters or {}).get("policy_approved", False)),
            timeout_seconds=int((request.parameters or {}).get("timeout_seconds") or 45),
        )
        payload = self.adapter.execute(tool_request)
        return TaskResult(
            task_id=request.task_id,
            status=_map_status(payload.get("status")),
            detail=str(payload.get("detail") or payload.get("status") or "Skill execution finished."),
            failure_category=str(payload.get("failure_category") or "").strip() or None,
            artifacts={"result": payload},
            evidence={"bridge_mode": True},
            next_actions=list(payload.get("next_actions") or []),
            module_name="skill-browser-session",
            capability=request.capability,
        )


def healthcheck() -> dict[str, Any]:
    return Skill().healthcheck().as_dict()

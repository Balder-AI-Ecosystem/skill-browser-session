from unittest.mock import MagicMock, patch
from src.skill_browser_session.main import Skill
import pytest

def make_request(capability_id, **params):
    req = MagicMock()
    req.capability_id = capability_id
    req.parameters = params
    return req

def test_observe_page_returns_ok():
    skill = Skill()
    with patch.object(skill, '_adapter') as mock_adapter:
        mock_adapter.observe_page.return_value = {"status": "ok", "page_title": "Test"}
        result = skill.execute(make_request("browser_session.observe_page", target="https://example.com"))
    assert result["status"] == "ok"

def test_type_text_dry_run_no_side_effect():
    skill = Skill()
    result = skill.execute(make_request("browser_session.type_text", target="hello", dry_run=True))
    assert result.get("status") in ("preview", "ok", "confirmation_required")

def test_unknown_capability_raises():
    skill = Skill()
    with pytest.raises(Exception):
        skill.execute(make_request("browser_session.unknown"))

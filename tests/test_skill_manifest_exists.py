from skill_browser_session.main import Skill


def test_skill_manifest_exists() -> None:
    manifest = Skill().manifest()

    assert manifest.name == "skill-browser-session"
    assert "browser_session.observe_page" in manifest.capability_ids()
    assert "browser_session.click_text" in manifest.capability_ids()

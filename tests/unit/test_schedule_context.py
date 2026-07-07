"""Regression tests for runtime schedule context copy."""

from ai_companion.modules.schedules.context_generation import ScheduleContextGenerator


def _all_schedule_activities() -> list[str]:
    activities: list[str] = []
    for day in range(7):
        activities.extend(ScheduleContextGenerator.get_schedule_for_day(day).values())
    return activities


def test_schedule_context_uses_support_companion_framing() -> None:
    activities = _all_schedule_activities()

    assert len(activities) == 84
    assert any("Support window" in activity for activity in activities)
    assert any("grounding" in activity for activity in activities)
    assert any("Consent-first ritual frame" in activity for activity in activities)
    assert any("Late-night tone" in activity for activity in activities)

    joined = " ".join(activities).lower()
    overclaiming_phrases = [
        "rose begins",
        "rose prepares",
        "rose practices",
        "rose engages",
        "rose rests",
        "rose takes",
        "rose studies",
        "rose creates",
        "rose spends",
        "her garden",
        "her body",
        "her spirit",
        "lineage",
        "cure",
        "healing session",
        "healing journey",
        "healing space",
        "healing work",
        "therapeutic",
        "emotional healing",
    ]

    for phrase in overclaiming_phrases:
        assert phrase not in joined


def test_schedule_context_returns_empty_schedule_for_unknown_day() -> None:
    assert ScheduleContextGenerator.get_schedule_for_day(7) == {}

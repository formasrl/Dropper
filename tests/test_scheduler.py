from __future__ import annotations

from src.scheduler import TriggerScheduler


def test_any_overlay_cooldown_blocks_all_categories():
    scheduler = TriggerScheduler(min_seconds_between_any_overlay=240)
    scheduler.record_trigger("random", 0)
    decision = scheduler.can_trigger("drop", 100)
    assert not decision.allowed
    assert decision.reason == "cooldown_any_overlay"
    assert decision.cooldown_remaining_sec == 140


def test_drop_cooldown_blocks_drop_after_any_cooldown_has_passed():
    scheduler = TriggerScheduler(
        min_seconds_between_any_overlay=60,
        min_seconds_between_drop_overlays=420,
    )
    scheduler.record_trigger("drop", 0)
    decision = scheduler.can_trigger("drop", 120)
    assert not decision.allowed
    assert decision.reason == "cooldown_drop_overlay"


def test_max_drop_overlays_per_hour():
    scheduler = TriggerScheduler(
        min_seconds_between_any_overlay=0,
        min_seconds_between_drop_overlays=0,
        max_drop_overlays_per_hour=2,
    )
    scheduler.record_trigger("drop", 0)
    scheduler.record_trigger("drop", 100)
    assert not scheduler.can_trigger("drop", 200).allowed
    assert scheduler.can_trigger("random", 200).allowed

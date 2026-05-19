from __future__ import annotations

from src.state_machine import ShowState, StateMachine, StateSignals


def test_build_to_preroll_when_confidence_is_high():
    machine = StateMachine(confidence_threshold=0.78)
    assert machine.transition(StateSignals(calibration_done=True)) == ShowState.NORMAL
    assert machine.transition(StateSignals(bass_suppressed=True)) == ShowState.BREAKDOWN_CANDIDATE
    assert (
        machine.transition(StateSignals(bass_suppressed=True, energy_rising=True))
        == ShowState.BREAKDOWN
    )
    assert (
        machine.transition(StateSignals(energy_rising=True, onset_density_rising=True))
        == ShowState.BUILD
    )
    assert machine.transition(StateSignals(confidence=0.8)) == ShowState.PREROLL_ARMED
    assert machine.transition(StateSignals()) == ShowState.PREROLL_PLAYING


def test_pause_and_resume():
    machine = StateMachine(state=ShowState.NORMAL)
    assert machine.transition(StateSignals(pause_requested=True)) == ShowState.PAUSED
    assert machine.transition(StateSignals()) == ShowState.PAUSED
    assert machine.transition(StateSignals(resume_requested=True)) == ShowState.NORMAL


def test_unhealthy_audio_enters_error():
    machine = StateMachine(state=ShowState.NORMAL)
    assert machine.transition(StateSignals(audio_healthy=False)) == ShowState.ERROR

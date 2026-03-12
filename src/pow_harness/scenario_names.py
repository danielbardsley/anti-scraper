from enum import StrEnum


class ScenarioName(StrEnum):
    SINGLE_SESSION_BASELINE = "single-session-baseline"
    SINGLE_SESSION_FAN_OUT = "single-session-fan-out"
    OUTSTANDING_CHALLENGE_PRESSURE = "outstanding-challenge-pressure"
    STALE_CHALLENGE_SPEND = "stale-challenge-spend"
    EXPIRY_EDGE = "expiry-edge"

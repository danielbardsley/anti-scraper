from enum import StrEnum


class ScenarioStopReason(StrEnum):
    REQUEST_CAP_REACHED = "request_cap_reached"
    DURATION_CAP_REACHED = "duration_cap_reached"
    ITERATION_TARGET_REACHED = "iteration_target_reached"

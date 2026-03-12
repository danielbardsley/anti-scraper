from enum import StrEnum


class ErrorBucket(StrEnum):
    SUCCESS = "success"
    SESSION_REQUIRED = "session_required_or_invalid"
    IP_CHALLENGE_RATE_LIMITED = "challenge_rate_limited_by_ip"
    SESSION_CHALLENGE_RATE_LIMITED = "challenge_rate_limited_by_session"
    TOO_MANY_OUTSTANDING_CHALLENGES = "too_many_outstanding_challenges"
    STALE_CHALLENGE_DIFFICULTY = "stale_challenge_difficulty"
    CHALLENGE_EXPIRED = "challenge_expired"
    CHALLENGE_ALREADY_CONSUMED = "challenge_already_consumed"
    REQUEST_BINDING_MISMATCH = "request_binding_mismatch"
    INVALID_PROOF = "invalid_proof"
    TRANSPORT_FAILURE = "transport_or_network_failure"
    UNKNOWN = "unknown"

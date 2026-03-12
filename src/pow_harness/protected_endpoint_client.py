from __future__ import annotations

from time import perf_counter

import httpx

from pow_harness.api_response_classifier import ApiResponseClassifier
from pow_harness.error_bucket import ErrorBucket
from pow_harness.protected_request_result import ProtectedRequestResult
from pow_harness.target_definition import TargetDefinition


class ProtectedEndpointClient:
    def __init__(self, classifier: ApiResponseClassifier):
        self._classifier = classifier

    def submit_proof(
        self,
        *,
        client: httpx.Client,
        target: TargetDefinition,
        request_body: dict,
    ) -> ProtectedRequestResult:
        started_at = perf_counter()
        try:
            response = client.post(
                f"{target.base_url}{target.protected_endpoint}",
                json=request_body,
            )
        except httpx.HTTPError:
            return ProtectedRequestResult.from_result(started_at, ErrorBucket.TRANSPORT_FAILURE, None)
        payload = response.json()
        bucket = self._classifier.classify(response.status_code, payload)
        return ProtectedRequestResult.from_result(started_at, bucket, payload)

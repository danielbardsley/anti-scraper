from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from proof_of_work_api.models.proof_payload import ProofPayload


class RandomNumbersRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    count: int | None = Field(None, ge=1)
    challenge_id: str = Field(..., alias="challengeId", min_length=1)
    proof: ProofPayload

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ChallengeIssueRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    resource: str = Field("random-numbers", min_length=1, max_length=64)
    count: int | None = Field(None, ge=1)

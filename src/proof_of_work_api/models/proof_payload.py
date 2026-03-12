from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProofPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    nonces: list[str] = Field(..., min_length=1)
    solver_started_at: str | None = Field(None, alias="solverStartedAt")
    solver_finished_at: str | None = Field(None, alias="solverFinishedAt")

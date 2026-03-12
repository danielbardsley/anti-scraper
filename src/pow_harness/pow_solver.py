from __future__ import annotations

from abc import ABC, abstractmethod

from pow_harness.solver_result import SolverResult


class PowSolver(ABC):
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def solve(self, challenge: dict) -> SolverResult:
        raise NotImplementedError

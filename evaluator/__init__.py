"""Evaluator package — sole owner of ground truth.
평가기 패키지 — ground truth의 단독 보유자.
"""

from evaluator.evaluator import Evaluator, GroundTruthTrial, ScoreResult

__all__ = ["Evaluator", "GroundTruthTrial", "ScoreResult"]

"""Oracle package — ceiling-reference controllers with ground-truth
access. Deliberately OUTSIDE controller/ so the banned-token CI gate on
rule-blind controllers stays meaningful.
oracle 패키지 — ground truth에 접근하는 상한선 참조 컨트롤러. rule-blind
컨트롤러에 대한 금지어 CI 게이트가 의미를 유지하도록 의도적으로
controller/ 바깥에 둔다.
"""

from oracle.oracle_full import OracleFullController

__all__ = ["OracleFullController"]

"""Oracle package — oracle-assisted policy-reference controllers (NOT ceilings) with ground-truth
access. Deliberately OUTSIDE controller/ so the banned-token CI gate on
rule-blind controllers stays meaningful.
oracle 패키지 — ground truth에 접근하는 oracle 보조 정책 참조 컨트롤러(상한선 아님). rule-blind
컨트롤러에 대한 금지어 CI 게이트가 의미를 유지하도록 의도적으로
controller/ 바깥에 둔다.
"""

from oracle.oracle_full import OracleFullController

__all__ = ["OracleFullController"]

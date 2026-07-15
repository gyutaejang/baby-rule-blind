# Deviations from the frozen analysis plan
# 동결된 분석계획으로부터의 변경 기록

Every change to `ANALYSIS_PLAN.md` after the freeze commit must be logged
here with the date, the change, and the reason. An empty log means the
study followed the plan exactly.

동결 커밋 이후 `ANALYSIS_PLAN.md`에 대한 모든 변경은 날짜·내용·사유와 함께
여기에 기록한다. 이 로그가 비어 있다는 것은 연구가 계획을 그대로 따랐다는
뜻이다.

| Date / 날짜 | Change / 변경 내용 | Reason / 사유 |
|---|---|---|
| 2026-07-15 | Amendment A (v1.1, §10): reframed as out-of-model transfer; Study 2 models = Claude Fable 5 / Opus 4.8 / Sonnet 5 + OpenAI flagship & mid tier (Haiku excluded); per-model generation configs (thinking off where possible, minimized on Fable 5); pre-registered headroom gate (RawLLM mean persistence ≥ 3.0), non-inferiority margin (−0.02), safety metrics, same-task rule, external freeze timestamping, development-contact ledger. / 수정안 A: 모델 외부 전이로 재구성, 모델·설정·게이트·마진 사전 등록. | Adopted BEFORE study2-freeze and before any Study 2 data existed — a pre-freeze design amendment, not a post-hoc change. Old models are being deprecated; transfer to current generations is both necessary and the stronger claim. / study2-freeze 및 Study 2 데이터 생성 이전의 사전 수정안. 구모델 지원 종료 대응이자 더 강한 주장으로의 전환. |

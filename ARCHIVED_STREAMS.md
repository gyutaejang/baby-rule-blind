# Archived stream provenance / 보관 스트림 출처

The 60 public streams in `data/public/` were extracted from the original
`brain like` project (see `data/manifest.csv` for per-file SHA-256 of
sources and outputs). Provenance, verified against the original runners
(`outputs_v2/zenodo_upload/llm_wcst_api_runner.py` and the ablation
runner in the original repository):

`data/public/`의 공개 스트림 60개는 원본 `brain like` 프로젝트에서
추출되었다(원본·산출 파일별 SHA-256은 `data/manifest.csv`). 원본 runner로
검증한 출처는 다음과 같다:

| Property / 항목 | Value / 값 |
|---|---|
| Claude streams (30) | model `claude-sonnet-4-6` |
| GPT streams (30) | model `gpt-4o` |
| Sampling / 샘플링 | temperature 1.0 (both / 양쪽) |
| Interaction / 상호작용 | single-turn per trial; no history, no feedback to the LLM / trial별 단일 턴, 이력·피드백 없음 |
| Collected / 수집 | 2026-04 (April 10, per source file timestamps / 원본 파일 시각 기준 4월 10일) |
| Schedule / 일정 | one fixed 36-trial schedule shared by all 60 streams / 60개 모두 동일한 고정 36-trial 일정 |

Role in this project (ANALYSIS_PLAN.md §10.7, §11): **development set
only** — controller design, parameter search, and all Study 1 analyses.
These streams never serve as confirmatory evidence.

본 프로젝트에서의 역할(ANALYSIS_PLAN.md 10.7절, 11절): **개발 데이터
전용** — 컨트롤러 설계, 파라미터 탐색, Study 1 분석 전부. 확증 근거로는
절대 사용하지 않는다.

## Withdrawn manuscript reference / 철회 원고 참조

The withdrawn submission carries two identifiers, recorded here by role.
The relationship between the S- and D-prefixed numbering schemes is NOT
assumed; it will be stated only if confirmed by the journal.

철회 제출물에는 두 개의 식별 번호가 있으며 역할별로 기록한다. S-/D- 접두
체계의 관계는 추정하지 않으며, 저널이 확인해 줄 때에만 기술한다.

- Submission PDF / reference ID / 제출 PDF·인용용 ID: **COGSYS-S-26-00464**
- Editorial Manager display manuscript number / EM 표시 원고 번호
  (confirmed from the EM screen, 2026-07-15 / EM 화면에서 확인):
  **COGSYS-D-26-00370**
- Withdrawal request reference / 철회 요청 접수번호: 260715-008289
  (Elsevier Support, 2026-07-15)

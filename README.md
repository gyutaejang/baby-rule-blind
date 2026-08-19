# baby-rule-blind

Corrected redesign of the withdrawn Baby40 study (submission-PDF ID
COGSYS-S-26-00464; see ARCHIVED_STREAMS.md for the manuscript-ID note):
a **sparse outcome-feedback supervisor for memoryless LLM outputs** in
WCST-style rule-shift tasks, with strict information isolation. Ground
truth is readable by exactly two components: the evaluator (scoring) and
the `oracle/` package (the oracle-assisted policy reference condition,
explicitly exempt). Rule-blind controllers in `controller/` can read
neither.

철회된 Baby40 연구(제출 PDF ID COGSYS-S-26-00464; 원고 ID 주석은
ARCHIVED_STREAMS.md 참조)의 교정 재설계: WCST형 규칙 전환 과제에서
**무기억 LLM 출력에 대한 희소 outcome-feedback supervisor**. 엄격한 정보
격리를 전제로 하며, ground truth를 읽을 수 있는 구성요소는 정확히 둘 —
평가기(채점)와 `oracle/` 패키지(명시적 예외인 oracle 보조 정책 참조
조건)다. `controller/`의 rule-blind 컨트롤러들은 어느 쪽도 읽을 수 없다.

## Key documents / 핵심 문서

- [`ANALYSIS_PLAN.md`](ANALYSIS_PLAN.md) — frozen analysis plan
  (conditions, roles, metrics, statistics). Read this first.
  동결된 분석계획(조건, 역할, 지표, 통계). 가장 먼저 읽을 것.
- [`DEVIATIONS.md`](DEVIATIONS.md) — log of any post-freeze changes.
  동결 이후 변경 기록.
- [`EXPLORATORY_INFORMATION_PROCESSING.md`](EXPLORATORY_INFORMATION_PROCESSING.md)
  — post-hoc information-processing analysis of the completed Study 2 replay;
  kept separate from the frozen confirmatory analysis.
- [`STUDY2B_PLAN.md`](STUDY2B_PLAN.md) — Study 2b (WCD-minimal) confirmatory
  plan; binding as of the `study2b-freeze` tag (see Freeze record below).
  Study 2b(WCD-minimal) 확증 계획; `study2b-freeze` 태그 시점부터 구속력
  (아래 동결 기록 참조).

## Freeze record / 동결 기록

Confirmatory claims are licensed by externally timestamped git tags, not
by document headers. 확증 주장의 근거는 문서 머리말이 아니라 외부
타임스탬프가 찍힌 git 태그다.

| Tag | Commit | Date | Scope / 범위 |
|---|---|---|---|
| `plan-freeze-v1.0` | — | pre-Study 2 | Analysis plan (`ANALYSIS_PLAN.md`) / 분석계획 동결 |
| `study2-freeze` | `43f6659` | 2026-07-15 | Study 2 confirmatory design, conditions, statistics / Study 2 확증 설계 |
| `study2b-freeze` | `0649cbc` | 2026-07-18 | Study 2b WCD-minimal spec with calibrated parameters (decay = 0.5, switch_margin = 0.0, wait_threshold = 1), S1 non-inferiority margin Δ = 1.9917, hypothesis hierarchy and interpretation map — fixed **before** generation of confirmatory repetitions 131–260 / Study 2b 사양·보정 파라미터·가설 위계·해석 지도, 확증 반복 131–260 생성 **이전** 고정 |

Note: the status line at the top of `STUDY2B_PLAN.md` still reads
"DRAFT — not frozen." That line describes the document's pre-freeze life
cycle and was not rewritten when the tag was cut; the `study2b-freeze`
tag is the authoritative freeze event, and at that tag every calibration
placeholder in the plan is filled with its frozen numeric value. The tag
and this record are additive documentation only — no tagged content has
been rewritten.

참고: `STUDY2B_PLAN.md` 첫머리의 상태 표기는 여전히 "DRAFT — not
frozen"이다. 이는 동결 이전 문서 수명주기를 서술한 문장으로, 태그 시점에
고쳐 쓰지 않았을 뿐이다. 권위 있는 동결 사건은 `study2b-freeze` 태그이며,
그 태그 시점의 계획서에는 모든 보정 자리값이 동결된 수치로 채워져 있다.
이 기록은 추가 문서화일 뿐, 태그된 내용은 일절 재작성하지 않았다.

## Planned layout / 예정 구조

```
controller/     # rule-blind controllers — ground-truth tokens banned by CI
                # rule-blind 컨트롤러 — ground truth 관련 토큰은 CI로 금지
evaluator/      # the ONLY package that may read ground_truth.csv
                # ground_truth.csv를 읽을 수 있는 유일한 패키지
data/
  public/       # public_stream.csv per repetition / repetition별 공개 스트림
  ground_truth/ # ground_truth.csv — never imported by controller/
tests/          # leak-prevention tests (mandatory) / 누출 방지 테스트(필수)
analysis/       # paired permutation / bootstrap analyses / 통계 분석
```

## Provenance / 출처

Original archived streams and the withdrawn manuscript live in the
separate `brain like` folder and are treated as read-only inputs
(Study 1, retrospective replay only).

원본 보관 스트림과 철회 원고는 별도의 `brain like` 폴더에 있으며 읽기
전용 입력으로만 취급한다(Study 1, 회고 재생 전용).

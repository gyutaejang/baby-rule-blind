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

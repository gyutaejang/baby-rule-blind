# baby-rule-blind

Corrected redesign of the withdrawn Baby40 study (COGSYS-S-26-00464):
an external **rule-blind** controller for a frozen LLM in WCST-style
rule-shift tasks, with strict information isolation between the
controller (public information only) and the evaluator (sole owner of
ground truth).

철회된 Baby40 연구(COGSYS-S-26-00464)의 교정 재설계: WCST형 규칙 전환
과제에서 고정된 LLM에 대한 외부 **rule-blind** 컨트롤러. 컨트롤러(공개
정보만 접근)와 평가기(ground truth 단독 보유) 사이의 엄격한 정보 격리를
전제로 한다.

## Key documents / 핵심 문서

- [`ANALYSIS_PLAN.md`](ANALYSIS_PLAN.md) — frozen analysis plan
  (conditions, roles, metrics, statistics). Read this first.
  동결된 분석계획(조건, 역할, 지표, 통계). 가장 먼저 읽을 것.
- [`DEVIATIONS.md`](DEVIATIONS.md) — log of any post-freeze changes.
  동결 이후 변경 기록.

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

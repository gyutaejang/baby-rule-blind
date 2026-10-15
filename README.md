# baby-rule-blind

Public repository for:

> Jang, G. T. (in press). Binary outcome-feedback supervision of memoryless LLM
> outputs under a budgeted intervention policy. *Cognitive Systems Research*.
> https://doi.org/10.1016/j.cogsys.2026.101525

Can a closed-loop system built around a trial-wise memoryless large language
model show feedback-dependent adaptive behavior without changing the model?
In a Wisconsin Card Sorting Test (WCST)-style task with an unannounced hidden
rule, a small external supervisor sees only the model's public choices and
one correctness bit per trial, and may override at most 9 of 36 trials.
Three pre-registered findings: (1) reshaping the output trajectory without
feedback raises diversity but not accuracy; (2) the correctness bit raises
accuracy by 12–17 percentage points on all four held-out model generations;
(3) an information- and budget-matched win-stay/lose-shift policy beats the
elaborate belief-tracking supervisor on every model, and Study 2b localizes
the elaborate policy's cost to its protection stack. The adaptive unit is the
supervised architecture (generation module plus external supervisor), not
the LLM alone.

무기억(trial 단위 history 없음) LLM을 둘러싼 폐루프 시스템이 모델 자체를
바꾸지 않고도 피드백 의존적 적응 행동을 보일 수 있는가? 숨은 규칙이 예고
없이 바뀌는 WCST형 과제에서, 작은 외부 감독자가 모델의 공개 선택과 trial당
정답 비트 하나만 보고 36 trial 중 최대 9회만 개입한다. 사전 등록된 결과
세 가지: (1) 피드백 없는 궤적 재조정은 다양성만 높이고 정확도는 못 높임,
(2) 정답 비트는 4개 held-out 모델 세대 모두에서 정확도를 12–17%p 높임,
(3) 정보·예산이 맞춰진 win-stay/lose-shift가 정교한 신념 추적 감독자를
모든 모델에서 이기며, Study 2b는 정교한 정책의 비용을 보호 장치 스택에
국한시킴. 적응의 단위는 LLM 단독이 아니라 감독 아키텍처(생성 모듈 + 외부
감독자)다.

## Design in one line / 설계 요약

Information isolation is enforced by construction and by CI. Ground truth is
readable by exactly two components: the evaluator (scoring) and the `oracle/`
package (the oracle-assisted reference condition, explicitly exempt). Every
rule-blind controller in `controller/` can read neither; a banned-token scan
and leak tests run on every push.

정보 격리는 구조와 CI로 강제된다. ground truth를 읽을 수 있는 구성요소는
정확히 둘, 평가기(채점)와 `oracle/` 패키지(명시적 예외인 oracle 보조 참조
조건)뿐이다. `controller/`의 rule-blind 컨트롤러는 어느 쪽도 읽을 수 없고,
금지어 스캔과 누출 테스트가 모든 push에서 실행된다.

## Freeze record / 동결 기록

Confirmatory claims are licensed by externally timestamped git tags, not by
document headers. 확증 주장의 근거는 문서 머리말이 아니라 외부 타임스탬프가
찍힌 git 태그다.

| Tag | Commit | Date (KST) | Scope / 범위 |
|---|---|---|---|
| `plan-freeze-v1.0` | `a7f8241` | 2026-07-15 | Analysis plan v1.0 (`ANALYSIS_PLAN.md`) / 분석계획 동결 |
| `pilot-freeze` | `6f290a6` | 2026-07-15 | Plan v2.0 + parser v2, before the engineering pilot / 계획 v2.0, 파일럿 전 |
| `pilot-freeze-v2` | `d1e0438` | 2026-07-15 | Re-freeze after the pilot (parser v3, answer-format line, pinned OpenAI IDs; `DEVIATIONS.md`) / 파일럿 후 재동결 |
| `study2-freeze` | `43f6659` | 2026-07-15 | Study 2 confirmatory design, conditions, statistics, before any confirmatory stream / Study 2 확증 설계, 확증 스트림 생성 전 |
| `study2b-freeze` | `0649cbc` | 2026-07-18 | Study 2b WCDMinimal spec with calibrated parameters (decay = 0.5, switch_margin = 0.0, wait_threshold = 1), S1 non-inferiority margin Δ = 1.9917, hypothesis hierarchy and interpretation map, before generation of repetitions 131–260 / Study 2b 사양·보정 파라미터·가설 위계, 반복 131–260 생성 전 |

Note: the status line at the top of `STUDY2B_PLAN.md` still reads "DRAFT —
not frozen." That line describes the document's pre-freeze life cycle and was
not rewritten when the tag was cut; the `study2b-freeze` tag is the
authoritative freeze event, and at that tag every calibration placeholder in
the plan is filled with its frozen numeric value. Tagged content has never
been rewritten.

참고: `STUDY2B_PLAN.md` 첫머리의 상태 표기는 여전히 "DRAFT — not frozen"이다.
동결 이전 문서 수명주기를 서술한 문장으로, 태그 시점에 고쳐 쓰지 않았을
뿐이다. 권위 있는 동결 사건은 `study2b-freeze` 태그이며, 그 태그 시점의
계획서에는 모든 보정 자리값이 동결된 수치로 채워져 있다. 태그된 내용은
일절 재작성하지 않았다.

## Key documents / 핵심 문서

- [`ANALYSIS_PLAN.md`](ANALYSIS_PLAN.md) — frozen analysis plan (conditions,
  roles, metrics, statistics). Read this first. / 동결된 분석계획. 가장 먼저
  읽을 것.
- [`STUDY2B_PLAN.md`](STUDY2B_PLAN.md) — Study 2b (WCDMinimal) confirmatory
  plan, binding as of `study2b-freeze`. / Study 2b 확증 계획.
- [`DEVIATIONS.md`](DEVIATIONS.md) — dated log of every post-freeze change,
  including non-scientific repository fixes. / 동결 이후 모든 변경 기록.
- [`ARCHIVED_STREAMS.md`](ARCHIVED_STREAMS.md) — provenance of the 60 Study 1
  streams. / Study 1 보관 스트림 출처.
- [`EXPLORATORY_INFORMATION_PROCESSING.md`](EXPLORATORY_INFORMATION_PROCESSING.md)
  — post-hoc analyses, kept separate from the confirmatory results. / 사후
  탐색 분석.
- [`STUDY3_FEASIBILITY_DESIGN.md`](STUDY3_FEASIBILITY_DESIGN.md) — exploratory
  design notes for follow-up work; nothing in it is frozen. / 후속 연구 설계
  노트(미동결).
- [`tools/supplement_s3.md`](tools/supplement_s3.md) — supplement section S3
  source. / 보충자료 S3.

## Layout / 구조

```
controller/      rule-blind supervisors: passthrough (RawLLM), trajectory_only,
                 wsls (WSLSBudgeted / WSLSUnlimited), rule_blind_full, yoked_random,
                 wcd_minimal (Study 2b). Ground-truth tokens banned by CI.
evaluator/       the ONLY package that scores against ground truth
oracle/          OracleFull reference condition (explicitly exempt from isolation)
study2/          frozen prompt template, parser v3, API clients, stream runner
replay/          harness + run_study1 / run_study2 / run_study2b (replay of frozen streams)
analysis/        paired_stats (frozen machinery), run_study2_stats, run_study2b_stats,
                 calibrate_wcd_minimal, param_search, power_simulation, exploratory_*
scripts/         generate_schedules, generate_stimuli, extract_streams, make_figures,
                 run_all_checks, verify_repository_security, check_banned_tokens
tests/           leak prevention, design invariants, parser fixtures, WCDMinimal, dry run
data/
  public/              Study 1: 60 archived streams (30 Claude Sonnet 4.6, 30 GPT-4o)
  ground_truth/        Study 1 schedule
  stimuli_study2/      Study 2/2b prompts, reps 1–260, from master seed 20,260,715
  ground_truth_study2/ Study 2/2b schedules, reps 1–260
  public_study2/       Study 2/2b raw streams: 4 models × 260 reps × 36 trials
                       (+ attempts logs and per-model generation manifests with SHA-256)
results/         study1_*, study2_*, study2b_* trials / summaries / paired statistics;
                 calibration, power simulation, exploratory tables
```

## Reproduce / 재현

Replay and analysis use the Python standard library only (verified on CPython
3.14; no third-party packages, no environment lock needed). Stream generation
additionally needs the pinned API clients in `requirements.txt`.

재생·분석은 Python 표준 라이브러리만 사용한다(CPython 3.14에서 검증). 스트림
생성에만 `requirements.txt`의 고정 버전 API 클라이언트가 추가로 필요하다.

```bash
python scripts/run_all_checks.py        # mandatory gates: security, banned tokens, leak tests, invariants, dry run
python -m replay.run_study1             # Study 1 (exploratory) replay of the 60 archived streams
python -m replay.run_study2             # Study 2 confirmatory replay, reps 1–130
python -m analysis.run_study2_stats     # Study 2 statistics -> results/study2_paired_stats.csv
python -m replay.run_study2b            # Study 2b confirmatory replay, reps 131–260
python -m analysis.run_study2b_stats    # Study 2b statistics -> results/study2b_paired_stats.csv
python scripts/make_figures.py          # data figures from the locked results CSVs (needs matplotlib;
                                        #  written as Figure_1–3 = published Figures 2–4; the architecture
                                        #  figure, published Figure 1, is hand-drawn)
```

Everything is seeded; identical inputs reproduce identical outputs byte for
byte. No result may be reported unless `run_all_checks.py` exits 0.

모든 과정은 시드가 고정되어 있어 동일 입력은 바이트 단위로 동일한 출력을
낸다. `run_all_checks.py`가 0으로 종료하지 않으면 어떤 결과도 보고할 수 없다.

## Data integrity / 데이터 무결성

Every Study 2/2b stream, attempts log, stimulus file, and schedule carries a
SHA-256 in its manifest, and the CI gate verifies all of them on every push.
Files under `data/` and `results/` are stored byte-exact (`.gitattributes`
disables line-ending conversion) because the manifest hashes were computed on
the files as written. Generating a repetition that already exists is refused
by the runner; re-runs must archive the originals first.

Study 2/2b의 모든 스트림·attempts 로그·자극·일정 파일은 manifest에 SHA-256을
갖고 있으며 CI 게이트가 매 push마다 전부 검증한다. `data/`·`results/`는
바이트 그대로 저장된다(`.gitattributes`로 줄바꿈 변환 차단). 이미 존재하는
반복은 runner가 생성을 거부한다.

## License / 라이선스

Code: [MIT](LICENSE). Data, results, and documentation:
[CC BY 4.0](LICENSE-DATA). If you use either, please cite the paper above.

코드는 MIT, 데이터·결과·문서는 CC BY 4.0. 사용 시 위 논문을 인용해 주세요.

## History / 이력

This repository is the corrected redesign of a withdrawn earlier study
(submission-PDF ID COGSYS-S-26-00464; see `ARCHIVED_STREAMS.md`). The 60
Study 1 streams were extracted read-only from that project and are used for
retrospective, exploratory replay only; every confirmatory result comes from
streams generated after the freeze tags above. The project's own earlier
claims and how they were refuted are documented in the paper (Section 5.6).

이 저장소는 철회된 이전 연구(제출 PDF ID COGSYS-S-26-00464)의 교정
재설계다. Study 1 스트림 60개는 그 프로젝트에서 읽기 전용으로 추출해 회고적
탐색 재생에만 쓰며, 모든 확증 결과는 위 동결 태그 이후 생성된 스트림에서
나온다. 이전 주장과 그 반증 과정은 논문 5.6절에 기록되어 있다.

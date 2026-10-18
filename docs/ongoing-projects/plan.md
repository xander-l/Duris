# Issue #59: complete and qualify the existing telemetry pipeline

Status: implementation plan only, prepared 2026-10-18. No telemetry activation,
gameplay changes, migrations, or production load tests are authorized by this plan.

- Work item: [#59 — Telemetry: fix reporting and capture visibility, then qualify continuous collection](https://github.com/LuminariMUD/Duris/issues/59).
- Source baseline: [`89253179ab1f89249634eeef9116653381e3d807`](https://github.com/LuminariMUD/Duris/commit/89253179ab1f89249634eeef9116653381e3d807), fetched `origin/master`.
- Publication base: [`9017ce1ca940cbe74a6162fca3d4d8c113eeb8b6`](https://github.com/LuminariMUD/Duris/commit/9017ce1ca940cbe74a6162fca3d4d8c113eeb8b6).
  Master advanced with #192 during planning; its PvP/privacy changes leave the
  telemetry modules and plan findings unchanged. Use the updated migration
  chain and preserve its privacy boundaries during implementation.
- Delivery branch: `branch/issue-59-telemetry-readiness`; this plan's seven tasks
  map directly to the seven unchecked work items in #59.
- The previous, unrelated issue #67 plan is preserved byte-for-byte in
  [plan-issue-67.md](plan-issue-67.md). Its unfinished work is not part of #59.

## Outcome and scope

Repair the existing producer → queue/worker → SQL → rollup/publication → report
path, expose capture loss independently of transport health, finish one useful
report/export journey, and produce a measured readiness decision for the current
shared host. Collection, saves, database writes, analytics, and backups must fit
together. Another machine is not an available fallback.

Reuse the bounded queue, dedicated telemetry worker, repository replay handling,
rollup transactions, report budgets/cache, reward projection, and native/SQL test
harnesses. Do not build a new telemetry service, dashboard, spool, scheduler, or
generic benchmarking framework. Do not raise the player capacity to 1,000 or add
every possible analytics report. Do not change XP/reward authority or balance.

If the required scope exceeds the host's measured budgets, reduce detail,
retention, or job frequency while preserving useful semantics and visible
coverage, then requalify. If that still fails, keep telemetry disabled and record
the infeasibility and remaining limitations explicitly.

## What the code actually establishes

The issue's 2026-10-13 review is useful historical evidence, not current runtime
proof. Comparing its baseline with this checkout found no changes under
`src/telemetry` or `scripts/telemetry`; some telemetry tests have changed.
The following findings were checked directly against the current source:

1. **Mixed-stream rejection is still present.**
   [rollup_engine.py](../../scripts/telemetry/rollup_engine.py),
   `_validate_common_row`, accepts only kinds 1–5 before scope filtering.
   `build_page_contributions` subsequently requires a logical session and handles
   only interval/lifecycle/checkpoint/gap/configuration semantics.
   [telemetry_types.h](../../src/telemetry/telemetry_types.h) defines kinds 1–8.
   Local probes reproduced rejection of kinds 6, 7, and 8 in both matching and
   unrelated environments. Merely widening `range(1, 6)` cannot fix the consumer.
2. **The SQL projection and scope rules have drifted.**
   [db_access.py](../../scripts/telemetry/db_access.py), `RAW_COLUMNS`, omits the
   progression, encounter, and combat payload columns. The writer's
   `encounter_fields` and `combat_summary_fields` in
   [telemetry_repository.c](../../src/telemetry/telemetry_repository.c) use
   `encounter_*`/`combat_*` scope and quality columns. These facts can lack a
   logical player session. They cannot be interpreted using only the common
   environment/season/session columns.
3. **Quality bit 9 is rejected.**
   [rollup_definitions.py](../../scripts/telemetry/rollup_definitions.py) sets the
   raw mask to `(1 << 9) - 1`, while the native contract includes cardinality
   overflow at `1 << 9`. The local probe reproduced this rejection independently
   of the kind mismatch. Reserved bits must remain invalid.
4. **Health is incomplete, rather than absent.**
   [telemetry_runtime.c](../../src/telemetry/telemetry_runtime.c),
   `telemetry_runtime_health_copy`, returns transport health. The existing
   snapshot, observer, logs, and `world telemetry` already expose queue and SQL
   failures. They lack the requested complete producer/refusal/occupancy and
   journal-success view. `worker_outage_guard::checkpoint` ignores checkpoint
   results. The existing `failed_checkpoint` case in
   [telemetry_runtime_outage.cc](../../tests/async/telemetry_runtime_outage.cc)
   explicitly expects healthy transport after failed journal writes; update that
   expectation without making telemetry failure stop gameplay.
5. **Several independent bounds exist.**
   [session](../../src/telemetry/telemetry_session.h) and
   [activity](../../src/telemetry/telemetry_activity.h) state have 256 slots;
   detached residents consume slots until retirement. The
   [configuration registry](../../src/telemetry/telemetry_config_private.h) has
   64 identities. [Encounter state](../../src/telemetry/telemetry_encounter.h)
   has 128 runs, 64 participants/run, and 256 events/run; combat summary state
   has 128 runs and 64 actor slots/run. These are code limits, not demonstrated
   supported player counts. `test_telemetry_runtime_exhaustion.py` primarily
   covers sequence exhaustion; its name does not prove slot/configuration tests.
6. **Both percentile implementations are wrong for the p99.9 caller.**
   [benchmark_272.py](../../scripts/telemetry/benchmark_272.py) and
   [telemetry_capacity_272_harness.cc](../../tests/async/telemetry_capacity_272_harness.cc)
   divide ranks by 100 but receive 999. On samples 1..10,000 the Python helper
   returned 10,000 instead of nearest-rank p99.9 = 9,990. Existing workloads are
   counts of synthetic interval records, not simulated players.
7. **Cost concerns are plausible, not measured host failures.**
   [gain_exp](../../src/world/limits.c) emits progression after the storage guard,
   including zero-applied attempts reaching that boundary. Repository source
   shows seven serial requests for the ordinary existing-session interval/XP
   path, plus batch boundaries; actual workloads include other paths and retries.
   [telemetry_outage.c](../../src/telemetry/telemetry_outage.c) rewrites/syncs a
   bounded journal; failed checkpoints restore the prior observation time, so
   the success-based cadence can permit repeated retries. Measure SQL, event
   mix, and fsync cost before prescribing an optimization.
8. **Reporting foundations already exist; the missing integration is real.**
   [report.py](../../scripts/telemetry/report.py) provides bounded published
   activity/playtime/cohort/return reports and explicitly lists progression and
   reward metrics as unavailable in that catalog. Reward projection/report
   definitions already exist separately. Encounter definitions are pure semantics.
   [rested_bonus.py](../../scripts/telemetry/studies/rested_bonus.py) is an existing
   non-writing evaluator, not the missing export adapter.
   [outage.py](../../scripts/telemetry/outage.py) is an offline evidence reader
   taking the writer's exclusive ownership lock; invoking it against an active
   writer is not a live coverage integration.

Not established in this planning pass: current production activation, actual
player/event mix, enabled/disabled latency, real SQL throughput, bytes per fact,
retention capacity, or host feasibility. Do not copy the historical review's
running-server status or microbenchmark results into fresh acceptance evidence.

## Implementation sequence

### T59-01 — Repair mixed-stream rollups

Primary files: `scripts/telemetry/{db_access,rollup_engine,rollup_definitions}.py`,
existing rollup fixtures/integration/SQL tests, and `docs/telemetry/ROLLUPS.md`.

- Extend the named SQL projection using the existing native column contract.
  Resolve scope, configuration, quality, and identity from the correct family;
  reject conflicting/partial identity rather than inventing a player session.
- Define handling explicitly: kinds 1–3 retain their current duration/session
  rules; kind 4 carries scoped or process-wide gaps; kind 5 advances the cursor
  without duration. Kinds 6–8 advance the activity consumer safely and preserve
  applicable quality without contributing fictitious playtime. The first report
  extension in T59-06 consumes the fields it actually needs.
- Accept all currently defined raw quality bits, including family-specific
  overflow quality. Keep derived rollup bits separate from raw producer bits.
- Valid records in other environments/seasons must advance the global cursor
  without contaminating target totals. Retain deliberate fail-closed handling
  for unknown schema/kind, invalid replay/envelope/scope, reserved bits, and
  malformed consumed payloads. Validate before committing a page; no catch-all
  exception handler that silently skips corrupt data.
- Preserve fixed high-water/keyset scans, atomic contributions plus cursor,
  checkpoint-as-absolute semantics, duplicate/conflict handling, publication
  generations, and rollback/lost-COMMIT reread behavior.

Proof: extend the current regressions with real serialized shapes for all eight
kinds, sessionless encounters/NPC/pet combat summaries, unrelated scopes,
process gaps, overflow bit 9, unknown bits, malformed rows, page boundaries,
identical retry, conflicting retry, and ambiguous commit. Then write those
records through the real C++ SQL repository, roll up, publish, and query a report
in a disposable database. Compare exact expected totals and cursor on retry.
The current discriminator-only probe is not that integration test.

### T59-02 — Expose producer and journal failures

Primary files: existing telemetry runtime/types/health/transport/config/session/
activity/encounter/combat modules, `src/cmd/actinf.c`, and `src/net/comm.c`.

- Extend the existing snapshot and observer. Report emission attempts, queue
  admissions, and committed unique facts by kind, with replay, quarantine, and
  refusal counts distinguished. Count retries as retries, not new facts.
- Separately count session/configuration admission failures that occur before a
  record exists. Use bounded reason counters for full session/activity/run/actor/
  event/configuration state, invalid/unknown configuration digest, allocator
  exhaustion, and downstream admission rejection where those paths exist.
- Expose occupied/maximum slots and current configuration availability. Reuse
  existing state/stat accessors; avoid periodic unbounded scans or new locks on
  gameplay paths. Keep game-thread state and worker snapshots race-free.
- Surface journal last successful checkpoint age, last attempt/error, failure
  count, and poisoned/pending-publication state independently of SQL health.
  Overall readiness must flag incomplete capture even with zero queue depth and
  healthy transport. Preserve rate-limited warning/recovery events and privacy.
- Define which counters reset with a producer lifetime and which loss evidence
  survives restart for T59-06. A successful later sample cannot erase a lost
  observation interval. Version journal data only if additional persisted fields
  are necessary; older evidence must remain readable with explicit limitations.

Proof: extend native fixtures for the 257th resident session, detached occupancy
and retirement, the 65th configuration identity, unknown property digests, actor/
event exhaustion, and post-startup journal failure. Use a healthy fake repository
with an empty drained queue for focused capture tests, then repeat the material
cases with healthy real SQL in the integration journey. Verify staff output,
bounded logging, recovery, and no gameplay/save dependency on telemetry health.

### T59-03 — Fix benchmark statistics and measure representative gameplay

Primary files: existing benchmark and capacity harness, runtime/gameplay adapter
tests, `tests/async/run_telemetry_player_journey.py`, and performance-gate docs.

- Use one documented nearest-rank convention in both percentile implementations,
  with units that represent 99.9 exactly. Test a sufficiently large known sample
  where p99.9 differs from maximum, plus empty/small samples. Report sample count
  and maximum separately; small-sample p99.9 is not evidence of tail capacity.
- Reuse the player journey and fixtures to drive the same commands, movement,
  combat, XP, group changes, reconnects, detached sessions, and ordinary saves
  with telemetry disabled and enabled. Pin fixture, seed, build, configuration,
  database state, warm-up, and host conditions; repeat and alternate run order.
- Cover 50, 200, and 256 resident sessions, then overflow/churn. Independently
  vary run and actor occupancy, exercise more than 64 successive actors, roster
  churn through the 256-event limit, 64/65 configurations, and unknown digests.
  Include encounter-close/control bursts against nearly full queues. Overflow
  tests require visible refusal, not a claim that overload must lose nothing.
- Separate capture-only cost, real SQL plus journal cost, and concurrent
  rollup/report/reward-job cost. All run on the same representative host budget
  as the game and authoritative saves. Synthetic record microbenchmarks remain
  useful lower-level checks and retain their honest labels.
- Record command, pulse, and save latency distributions; game/worker CPU and RSS;
  attempted/admitted/committed rates by kind; occupied slots and refusals; queue
  depth/oldest age; SQL request, lock, and commit latency; fsync latency; durable
  and publication lag. Keep sanitized machine-readable results under `bin/` and
  commit a concise evidence summary with source/build/config identity.

Run in isolated local/dev infrastructure first. A representative shared-host
load run or activation affecting production requires its separate operational
authorization. Set trial duration from sufficient samples and observed journal/
rollup behavior; do not impose an arbitrary 24–48-hour wait. Extend the soak
until retained-history growth, steady-state behavior, and catch-up are observed.
Accelerated fault/history fixtures prove boundaries, not sustained host cost.

### T59-04 — Establish storage and operational budgets

Primary files: existing telemetry database/storage/performance/operations docs,
bounded operational scripts only where required, and the lifecycle manifest if
a retention policy is added. Reuse the repository's migration contract.

- Measure row counts by kind, representative payload sizes, table/index allocated
  bytes, aggregate cardinality, and growth during T59-03. Shared InnoDB pages do
  not provide exact per-kind byte attribution: use controlled per-kind deltas
  and report allocation/fragmentation uncertainty rather than false precision.
- Calculate daily storage from measured rates and measured size, including raw,
  aggregates/membership, configuration, reward projections, journal archives,
  backups, and rebuild space. Measure backup/restore and rollup rebuild cost.
- Record explicit raw/aggregate/journal retention, maximum telemetry disk use,
  warning/stop free-space thresholds, job cadence/connection limits, and maximum
  acceptable durable/publication/cache age. These values are chosen from actual
  host headroom and agreed operating needs, not copied from synthetic guards.
- Retention must preserve configuration references, replay/rebuild requirements,
  consumer watermarks, reward reconciliation acknowledgements, and unresolved
  quarantine/evidence. Use bounded resumable pruning with dry-run and restart
  proof if pruning is needed; do not delete authoritative reward sources merely
  because analytics is caught up.
- Document an operational owner and alert destination, activation prerequisites,
  deliberate environment/season/version identities, property-catalog updates,
  stop/restart/circuit recovery, pending-journal recovery, backup/restore order,
  and rollback triggers. Configure/check mechanisms locally; production changes
  remain a separately authorized application of the completed runbook.

Proof: measured budget worksheet/results, local alert threshold exercise,
retention dry-run/apply/retry on disposable data, and restore/rebuild yielding
the same scoped totals and explicit coverage. No unqualified retention defaults.

### T59-05 — Bound journal retries and qualify failures with saves

Primary files: `telemetry_runtime.c`, `telemetry_outage.c`, existing outage,
transport, repository, runtime, and SQL journey fixtures.

- Track the next permitted journal attempt independently of the last successful
  observation. Apply bounded retry pacing on failure; notification traffic must
  not bypass it. Keep last-success/error evidence visible, retain the last good
  frame, and never overwrite poisoned/pending evidence without validated recovery.
  Preserve terminal sampling without introducing an unbounded retry loop.
- Exercise SQL disconnect/reconnect, initialization failure, permanent refusal,
  lost commit acknowledgement, disk full, write/fsync/rename failure, delayed
  SQL/filesystem I/O, process crash, copyover, and shutdown. Retain existing
  savepoint isolation and reconcile ambiguous commits before later batches.
- Run these with ordinary player saves and concurrent rollup/report/reward jobs.
  Demonstrate game continuity, bounded telemetry retry work, visible incomplete
  coverage, and recovery without duplicate facts or totals. Verify ordinary
  saves remain correct independently of telemetry loss.
- Include pre-emission combat state and RAM queue loss on crash. The journal
  describes evidence; it cannot replay lost payloads. Distinguish nonblocking
  stop requests from eventual worker reap under delayed I/O; connector timeouts
  alone are not proof of a hard shutdown deadline.

Proof: extend `telemetry_runtime_outage.cc` and the existing fault harness with
attempt-count/time assertions, durable-frame checks, and observer transitions.
Use a controlled injected clock where available, plus real SQL restart/retry
journeys. Recheck T59-03 cost/freshness after changing retry behavior.

### T59-06 — Finish one useful report/export path with honest coverage

Primary files: existing rollup definitions/engine/SQL adapter, report service,
outage reader, reward/encounter definitions, study contract, and focused tests.

First deliver the existing activity/playtime/return reports plus the observed-XP
projection needed for a bounded rested-study export. Reuse the current evaluator.
This does not require building the full encounter/combat analytics catalog.
Every family still gets an explicit supported/unavailable disposition, and all
eight raw kinds must pass the integrated capture-to-report journey.

- Publish capture/coverage evidence with report generations, not just cursor
  freshness. Correlate producer identity, scope, known dropped/refused ranges,
  journal last-success/unknown tails, quarantine, and publication/cache age.
  Missing evidence is unknown/incomplete, never an inferred zero or completeness.
- Make the existing outage decoder usable through a bounded read-only snapshot
  path while the writer is active. Preserve the writer's ownership lock; do not
  make reporting acquire it or repair/delete pending files. Validate atomic
  published frames/checksum/generation and expose stale/pending/ambiguous evidence.
  Import evidence idempotently with the publication it qualifies; old cached
  pages must retain their evidence identity and show freshness limitations.
- Define XP as observed mutable requested/computed/applied amounts and counts,
  grouped by source/reason/modifier/configuration/level boundaries. Preserve
  zero-applied attempts; keep level-threshold consumption out of earned/lost XP
  totals. A committed telemetry row does not make observed XP an authoritative
  persisted reward. XP/hour uses matched covered exposure and null denominators.
- Reuse encounter definitions: attempts include all terminal outcomes; elapsed
  run time, participant effort, expected credit, and actual rewards are distinct.
  Combat actor/owner identity and cardinality loss remain explicit. Incomplete
  or unclosed runs cannot fabricate duration or successful outcomes. Specify
  these semantics before adding any further reports.
- Reuse the committed reward projection and its existing report definition.
  Currency/epic/combat-frag ledgers remain amount authorities; context rows are
  not added as rewards. Preserve source identity, reconciliation, retention-floor
  acknowledgement, late arrival, and conflict behavior. Do not create another
  reward writer or infer committed rewards from XP/encounter notifications.
- Map published return/playtime/progression data into the existing bounded study
  schema. Audit availability of rested-tier exposure, configuration/cohort
  boundaries, censoring, and approved redacted subject/repeat-group tokens.
  XP modifier flags alone do not prove a subject's entire exposure in a tier.
  Add only the missing capture/projection fields needed for this journey, using
  additive migration/versioning where necessary. Do not infer account identity
  from a subject ID or expose account/player identifiers in the export.
- Keep the evaluator SQL-free and non-writing. Synthetic qualified fixtures
  must remain `fixture_qualified`; missing inputs/coverage must abstain with
  reasons. An adapter that always abstains is not completion: demonstrate a
  complete synthetic source-to-export success and incomplete-source controls,
  and track real-data qualification separately from adapter correctness.

Proof: real SQL ingest → rollup → publication → bounded read-only report →
redacted export → evaluator; exact totals/denominators, source/config lineage,
idempotent retries, unavailable fields, stale cache, and outage-induced abstention.
Extend existing report/study/reward tests. If new aggregate/evidence columns are
needed, append migrations and update manifests/grants/bootstrap verification;
never edit sealed migrations or give report readers raw/live-game write access.

### T59-07 — Optimize only demonstrated bottlenecks and decide readiness

Use T59-03 through T59-06 evidence to name the limiting resource. If no material
bottleneck is found, record that result and make no optimization change.

Candidate fixes are fewer serial repository calls, configuration reuse within a
batch, bounded actor lookup changes, or reduced collection/report frequency.
Preserve original replay identity/payload equality, per-record savepoint isolation,
and ambiguous-commit recovery. Any XP coalescing/sampling must retain attempted
and applied amounts, zero-application evidence, source/modifier semantics, and
configuration/level boundaries. Define coverage before reducing detail.

Rerun only the affected correctness checks and matched measurements after each
change. If scope must shrink, repeat the entire relevant report/coverage journey
at that scope. Record one final disposition: ready within measured limits,
conditionally ready with explicit unmet gates, or not feasible/disabled.

## Verification and closure

For changed C/C++ run `./scripts/format.sh --check` and `make -C src`; exercise
applicable SQL and flat-file build/test variants. Follow
[TESTING.md](../guides/TESTING.md) for isolated databases and migration validation.
Use the smallest relevant executable tests while developing; expand only when
dependencies or failures justify it. Do not wait for hosted CI to establish local
proof, and do not bypass review requirements.

Existing starting points, to extend rather than duplicate:

```sh
python3 tests/async/telemetry_rollup_engine_test.py
python3 tests/async/test_telemetry_reports_contract.py
tests/async/with_disposable_mariadb.sh python3 tests/async/test_telemetry_repository.py --sql-fixture
tests/async/with_disposable_mariadb.sh python3 tests/async/run_telemetry_schema_boot_journey.py --server "$(realpath bin/server/dms_new)"
python3 tests/async/test_telemetry_health.py
python3 tests/async/test_telemetry_runtime_integration.py
python3 tests/async/test_telemetry_runtime_exhaustion.py
python3 tests/async/test_telemetry_runtime_outage.py
python3 tests/async/test_telemetry_config.py
python3 tests/async/test_telemetry_encounters.py
python3 tests/async/test_telemetry_combat_summary.py
python3 tests/async/test_telemetry_progression.py
python3 tests/async/test_telemetry_capacity_272.py
python3 tests/async/test_telemetry_fault_272.py
python3 tests/async/test_telemetry_reward_projection.py
python3 tests/async/test_telemetry_study_rested.py
python3 tests/async/test_telemetry_balance_shadow_recommend.py
python3 tests/async/test_telemetry_balance_apply_contract.py
```

The current SQL report runner installs only the original storage/rollup schema,
and current rollup SQL fixtures expect five kinds. Extend their isolated setup
to the required current schema and all families; existing green tests alone do
not prove the mixed pipeline. Reuse the player journey's task-owned local database
guards and the repository's maintained MySQL/MariaDB compatibility checks.

Before claiming readiness, record the selected absolute command/pulse/save
latency budgets, CPU/RSS/disk/I/O headroom, job freshness, and storage limits.
The issue's ≤5% matched pulse/save p99 regression is a proposed gate, not an
already-agreed guarantee. Enforce both relative and absolute budgets; report
sample counts, repeated-run variation, and measurement limitations.

- [ ] T59-01: all eight kinds handled; valid irrelevant rows advance; malformed
  records retain explicit failure handling; real SQL/report replay proof.
- [ ] T59-02: capture/refusal/occupancy/configuration/journal health visible with
  healthy SQL and an empty queue; recovery does not erase missing coverage.
- [ ] T59-03: corrected percentiles; matched gameplay at 50/200/256 plus independent
  overflow/churn/configuration/combat cases; complete metric evidence.
- [ ] T59-04: measured storage/growth/backup/rebuild, retention and alerts,
  explicit ownership and rehearsed stop/restart/recovery procedures.
- [ ] T59-05: bounded retries and fault/recovery proof alongside player saves and
  analytics; continuity and coverage preserved without duplicate totals.
- [ ] T59-06: useful published report/export succeeds; loss/staleness abstains;
  XP/encounter/combat/reward/study semantics and unavailable capabilities explicit.
- [ ] T59-07: measured optimization or justified no-change decision; final host
  feasibility and readiness disposition with supporting evidence.

Normal supported load must have no admission/control loss, no slot overflow, no
sustained backlog, and writer/rollup service above measured peak input with
explicit headroom. Injected overload/outages must expose loss and recover without
double counting. A caught-up cursor is never sufficient capture proof.

Maintain each task's result, commit, command, evidence location, and unresolved
gate here. Link implementation PRs to #59; keep the issue open while required
evidence or an explicit disposition is missing. Publication of this plan does
not close the issue, establish production readiness, or authorize deployment.

## Estimate and uncertainty

This work completes an existing subsystem. Estimate active implementation work
separately from benchmark runtime and operational scheduling.

Planning estimate for agent-driven work: **6–12 active hours for the first complete
local implementation and validation pass**, with low confidence until the first
SQL journey and study-input audit run. The working allocation is approximately
3–5 hours for compatibility/health/retry/statistics repairs and focused proof,
2–4 hours for report/coverage/export integration, and 1–3 hours for load/storage/
failure measurement setup, operational documentation, and evidence review.
These are estimates, not measured coding throughput or a delivery guarantee.

Benchmark/soak execution, review turnaround, and separately authorized shared-host
operations add elapsed time and can overlap editing. Choose test duration from
sample sufficiency, stable service rates, journal history, and catch-up; extend
only when those observations are missing. There is no automatic multi-day wait.

The main expansion risks are missing study exposure/identity inputs, real SQL
integration defects, and host interference requiring a smaller collection scope.
Re-estimate after T59-01 and the T59-06 input audit with exact additional work;
do not quietly add a report catalog, 1,000-player capacity, or infrastructure.
Full issue closure remains dependent on measured budgets and recorded dispositions,
even if the code changes finish sooner.

## Evidence from this planning pass

Executed on the pinned baseline, without a live database or game activation:

- `telemetry_rollup_engine_test.py`: **14 passed**.
- `test_telemetry_reports_contract.py`: **14 passed**.
- `test_telemetry_health.py`: **normal and ASan/UBSan harnesses passed**.
- Discriminator probes: kinds 6–8 rejected in matching and unrelated scopes;
  quality bit 9 rejected. These isolate validation and are not valid serializers
  for complete new-family records.
- Percentile probe: samples 1..10,000 produced 10,000 for the current `999` call;
  nearest-rank p99.9 is 9,990. The native implementation has the same denominator.

These passing component checks coexist with the reproduced defects. Full C/C++
builds, new regression cases, real SQL mixed ingestion/publication, gameplay
load, storage measurements, and production acceptance are implementation work
and were not performed merely to publish this documentation.

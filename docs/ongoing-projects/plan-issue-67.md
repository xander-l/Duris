# Finish issue #67 and merge it

**One delivery branch. Finish the gaps. Verify the complete result. Merge once.**
This replaces the checkpoint log without dropping any acceptance requirement.
Latest owner instruction: merge the accumulated work immediately without additional
tests or review loops. Current master integrated without conflicts. Remaining
acceptance items below are explicitly unfinished; this merge does not close #67.

## Starting point

- Worktree: `/home/aiwithapex/projects/duris-issue67-writer-backpressure`.
- Branch: `branch/issue-67-review-handoff`; [PR #184](https://github.com/LuminariMUD/Duris/pull/184).
- Verified starting head: `9187dd6199e88cc133cf30afbae110c3c865dd8c`.
- Refreshed master: `e07b51a6d84c4010a89a333b9cafc00d804717f2`; three commits not integrated.
- All **47 issue #67 PR heads are ancestors of this delivery head**. All remain open.
- [Immutable previous plan](https://github.com/LuminariMUD/Duris/blob/9187dd6199e88cc133cf30afbae110c3c865dd8c/docs/ongoing-projects/plan.md):
  complete branch/PR inventory, original AR-01–AR-08 requirements and historical proof.
  Consult it for evidence, not as another execution queue.

Already implemented: canonical identity/storage; qualified admission at reviewed
reset/staff/scripted and saved-owner paths; native NPC recovery; duplicate-safe
rewards and “from above” feedback; inspection/maintenance guards; swap placement
rollback; committed creation repair; full durable shop-stock reuse. Recorded SQL/flat
builds and focused tests passed. Remaining completeness/durability/audit/journey
requirements below are still open; do not reimplement the working pieces.

## Four steps to the finish line

### 1. Make the existing combined branch the single delivery PR

On execution, refresh refs, require a clean delivery checkout, confirm published
heads are included, and integrate current master into this branch once. Resolve
conflicts here. Retarget **#184 to master**, describe the complete result, and push
focused implementation commits to it. Preserve existing branches and PRs until landing.

Do not reconstruct/cherry-pick the stack or restack and merge 47 branches separately.
Their work is already combined. One final squash merge delivers it with linear history.

### 2. Close these three gaps using the existing code

**A. Finish admission and lifecycle coverage.** Inventory remaining `read_object`,
`instantiate_object_template` and `clone_obj` callers once. Change only reachable
gameplay/inspection paths missing the established boundary: `src/specs`, dynamic
quest/random-zone/encounter producers and periodic binding display in
`src/guild/artifact.c`. Reuse `artifact_admission`, qualified saved-UID construction
and template inspection. Preserve normal objects, saved flag overrides and valid
same-UID restoration; no blanket constructor ban. Extend existing source-inventory,
creation-admission and native-runtime fixtures.

**B. Finish durable retirement and swap.** Start at `arti_swap_finish` in
`src/guild/artifact.c`: placement rollback exists, but player/corpse saves and artifact
updates remain separate. Trace its existing snapshot/transfer repository path.
Make one accepted operation cover required payload, custody and artifact after-images
or retirement tombstone in each backend. Reuse the existing game-thread state and
writer; extend its operation only where it cannot express the whole transition.

Retain recoverable original bodies/state until submission acceptance; rollback refusal.
Define in-memory availability separately from durable retirement. Prove crash prefixes,
failed/ambiguous writes, retries and late acknowledgements cannot resurrect the old
copy, release a new claim or lose survivor UID/timer/soul/mana. Cover online/offline
player, corpse and supported world/storage destinations. Placement and enqueue success
alone do not prove durability. No second writer, authority, queue or synchronous fallback.

**C. Complete actual-instance/variant audit and reversible repair.** Extend
`scripts/classify_item_topology.py` and the existing artifact inventory for missing
domains only. Use synthetic data and an isolated development clone. Classify same-UID
projections, distinct-UID copies, stale/quarantined records and intentional variants.
Compare **32827/67281, 67280/98904, 902/914 and 923–926** using definitions, reset sites,
flags/stats, saved enhancements, compiled callbacks and dynamic procs.

Record an evidence-supported disposition for every confirmed conflict; preserve
intentional variants/enhancements. Never choose by traversal order, name or age.
Unknown intent remains reserved and explicitly gated on evidence/owner decision.
Rehearse dry-run/apply with an inventory digest, exact preconditions and rollback
evidence. Prove repeat-no-op, changed-evidence refusal and restart without resurrection.
Keep exact UID/owner/payload evidence private; commit aggregate results and the runbook.

### 3. Verify the combined result once against every gate below

After each code change, run its smallest affected regression. Reuse valid earlier
results where code/dependencies are unchanged. Extend existing tests, not another
framework. At the final source tree, run SQL and flat builds, changed-line formatting
and tidy, `make test-all`, and applicable isolated `make test-db` cases under
[TESTING.md](../guides/TESTING.md), including maintained MariaDB/MySQL compatibility.
Use ASan/UBSan for identity/lifetime rollback tests. New regressions must detect removal
of the relevant behavior guard, not merely changed source text.

Extend `tests/async/test_mysql_artifact_guild_reward_journey.py` and
`tests/async/run_world_recovery_journey.py` for missing integration coverage.
Complete the artifact journey on SQL and flat-file: creation/duplicate refusal,
transfer/equip/feed, save/logout/login, nest/store/drop, death/loot/raise,
expire/destroy, copyover, clean restart and crash recovery. Exercise Redis success,
disabled and failed/partial fallback where supported. Include legacy conflict
audit/apply/save/restart/repeat. Verify actual population and persisted state/feedback.

Use focused executable cases for independent mode/path combinations and the full
journey for integration; do not multiply every case into a Cartesian product.
Fix genuine failures and rerun affected checks. Broaden/repeat only when changes
invalidate evidence. Hosted CI is not a required wait. Do not add a hardening phase.

### 4. Merge and close out, rather than stopping at another review handoff

Inspect current review threads and body findings on #184 and the included stack.
Fix valid findings with relevant proof. Refresh master immediately before merging;
if it moved, integrate the new changes and rerun their affected checks.

Squash-merge **#184 into master**, guarded by the exact tested head and current
repository rules. Master requires a PR and linear history. Local integration merge
commits are absorbed by the squash. Do not force-push master or bypass requirements.

Read back the merge and remote master; compare the merged commit's tree to the tested
integration tree. If master advances afterward, compare the exact merge commit.
Only after equality is proved, close old PRs as **superseded by merged #184**, linking
the merge. Their code is merged; their PR objects are closed, not individually merged.
Preserve branches/WIP until disposition is clear. A code merge needs no arbitrary tag.

Update operational/staff guidance and this plan with actual merge/evidence. Prepare
release news when releasing. Prepare the concrete production audit/apply/rollback
procedure, backups/restore proof, exact commands, counts/hashes and rollback trigger.
Production audit/deployment/migration/repair still requires the separately authorized
procedure; ask only after it is concrete. Verify live population, feedback and
save/relogin/restart after authorized rollout. Keep #67 open for unmet production or
version acceptance; merged code is not evidence of repaired production data.

## Complete acceptance checklist

These gates preserve the original issue and AR-01–AR-08 scope. Attach a result/commit
to each. Existing proof counts where applicable; missing proof is not a reason to
rewrite already-correct code. Identify actual external evidence/owner gates explicitly.

- [ ] **Identity/all stores (AR-01/02):** one gameplay copy per artifact vnum; absent,
  canonical, reserved/unresolved and retired states. Online/offline players/pets,
  nested trees, NPCs, rooms, corpses, lockers, shops, auctions, collectors/delivery,
  recovery payloads. Correlate UID/vnum/root/parent/custody/revision/state. Partial or
  failed reads never prove absence; classify before population.
- [ ] **Creation/recovery (AR-01/03):** O/P/G/E, indirect/scripted producers, staff
  load/clone including container/mob trees, same-pulse attempts, boot, regular/forced
  reset, respawn **0/1/2**, **51005 limit three**, recovered NPCs, native copyover and
  Redis success/disabled/failure. Block duplicates without losing legitimate availability.
- [ ] **Restoration/inspection (AR-02/03):** exactly-once same-UID restoration; atomic
  failed-load rollback; offline/corpse protection; retained conflict payloads and
  unrelated inventory. Inspection cannot claim/feed/save/release/circulate an artifact.
  Staff gameplay creation follows the same uniqueness policy; no transferable exception.
- [ ] **Lifecycle/durability (AR-04):** nested moves, wear/unwear, mortal/staff/NPC
  transfers, trade/storage, death/loot/raise/decay, expiration, purge, deletion and
  `eat ... update`. Unloading is not retirement. Rejected copies cannot change
  survivor location/timer/soul/mana/persistence or enable spawning. `sync`, `syncdb`
  and `clear` cannot release a live claim. Crash/retry/late-ACK proof covers step 2B.
- [ ] **Rewards/feedback (AR-05):** canonical plus rejected copies in both equipment
  orders; cross-player copies; unrelated artifacts and guild-only results; thresholds,
  caps, PvP soul, no-effect/arithmetic/rejection controls. Preserve merged #58/#96,
  one delta per allowed vnum and immediate valid application. Emit “You feel a sense
  of satisfaction from above.” once at the valid boundary, including monolith
  coalescing; history retry/replay/restart never reapplies/repeats it. Diagnostics
  remain actionable, bounded and free of private player/account data.
- [ ] **Variants/repair (AR-06):** actual-instance classification, explicit confirmed
  conflict dispositions, stat/proc regressions, intentional variants/enhancements,
  protected provenance and reversible dry-run/apply/repeat/restart proof.
  Source inventory alone is not full behavioral qualification.
- [ ] **Qualification (AR-07):** permanent regressions, sanitizer rollback cases,
  actual SQL repositories and flat lifecycle, schema/legacy/FK/null/unowned compatibility,
  complete journey and required final suites. If migration is needed, use the immutable
  migration contract, checksums/bootstrap/legacy/replay proof; never edit sealed migrations.
- [ ] **Merged/closed out (AR-08):** complete code/docs reviewed and merged, tested-tree
  equality verified, old PRs linked/closed, current staff/runbook guidance, separately
  authorized production procedure and post-rollout evidence tracked. Close #67 only
  when its applicable acceptance criteria are met.

## Boundaries and compact resume record

Follow [AGENTS.md](../../AGENTS.md), [ADR 0002](../adr/0002-persistence-reset-memory-is-the-authority.md)
and the [reward contract](../persistence/CRITICAL_COMMAND_PIPELINE.md#artifact-and-guild-rewards-live-in-memory).
Keep mutable state on the game thread and immutable captures on the existing writer.
No SQL/Redis reads in movement/feed/reset hot paths. Preserve unrelated changes,
protected data, worktrees, variants and valid enhancements. Unrelated confirmed
defects stay separate and must not restart this issue's delivery cycle.

Preserved unused WIP: `branch/issue-67-artifact-compound-capture`, `c50475f85`,
in `/home/aiwithapex/projects/duris-issue67-plan`. Inspect only if step 2B needs it;
do not assume it works, discard it or include it wholesale. The immutable previous
plan indexes every historical branch and proof. Recent proof remains under ignored
`bin/analysis/shop-reuse-*.log` and `review-handoff-final-rewards.log`.

After each completed step, replace this record instead of appending another log:
**current head; next unmet gate; checks/results; PR/merge status; exact external blocker.**
Stop at complete verified delivery on master, with separately authorized production
work accurately accounted for—not at PR publication or an empty review queue.

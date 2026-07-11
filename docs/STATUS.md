# Status

## Current stage

M2.1: MBPP candidate review and related-task group selection — completed on 2026-07-11. M2.2 is the next stage and has not started.

M2.0 was integrated onto the pre-existing GitHub `main` history through a non-force cherry-pick. The preserved remote ancestor is `6fc58fae819a6d3f9d577904caf2b26e22263dda`; the M2.0 integration commit is `74d2b42bb5e52566be4154a8257dd17e99d10afc`.

On 2026-07-10, the Windows-to-openEuler SSH check succeeded, but openEuler repository synchronization and M2.0 acceptance remained blocked before GitHub access because the VM had no default route and `ping -c 3 1.1.1.1` returned `Network is unreachable`. A sudo-authorized NetworkManager restart was attempted; after restart, the VM still had no default route and external-IP connectivity remained unavailable.

Further host-side diagnosis found Windows external connectivity on `vEthernet (ExternalSwitch-Realtek)` with IPv4 `10.24.2.86/21`, gateway `10.24.0.1`, and working TCP 443 access to GitHub. In openEuler, `eth0` repeatedly attempted DHCP but received no lease, while `hyperv-nat` and `oa-hostonly` remained static connections without gateways. A temporary `eth0` static route trial was not applied because sudo authentication for `oa` did not succeed.

The usable openEuler external path was later identified as `eth1` on Hyper-V Default Switch with gateway `172.24.64.1`. A temporary runtime default route through `eth1` restored external IP reachability and GitHub DNS resolution. GitHub SSH on port 22 authenticated successfully as `Robbymee`, and `git ls-remote git@github.com:Robbymee/LiteTest-MAS.git` returned `main` at `6fc58fae819a6d3f9d577904caf2b26e22263dda`. Repository synchronization stopped because `~/LiteTest-MAS` is an existing Git repository on `master` with no remote and many untracked project files; it must not be overwritten without user approval.

## Completed baseline

- The Windows-to-openEuler minimum workflow is established.
- A01 Text Mode completed on openEuler.
- A01 Protocol Mode completed on openEuler.
- The recorded openEuler repository test result is `5 passed`.
- M2.0 management documents, offline MBPP-Sanitized importer, synthetic importer fixture, and importer tests are implemented.
- Windows-local acceptance recorded `6 passed` for `tests/test_mbpp_import.py` and `15 passed` for `tests/`.
- Windows-to-openEuler SSH remote command execution was revalidated on 2026-07-10.
- Windows M2.0 acceptance on 2026-07-11: `tests/test_mbpp_import.py` reported `6 passed`; `tests/` reported `15 passed`; `git diff --check` passed.
- openEuler M2.0 acceptance on 2026-07-11: openEuler 24.03-LTS-SP3, Python 3.11.6, `tests/test_mbpp_import.py` reported `6 passed`, `tests/` reported `15 passed`, and `git diff --check` passed.
- The openEuler validation log is `/home/oa/LiteTest-MAS/runs/validation/m2_0_openeuler-20260711-092254.log`.

## Not completed

- Human review and confirmation of the MBPP candidate groups; no final public-dataset task selection has been made.
- Ten-round public-dataset batch execution.
- HumanEval adaptation and validation.
- Formal Evaluator, real LLM backend, SharedMemory, and StateVector.
- Four ablation experiments, coverage/mutation metrics, Docker/iSulad sandbox, and Dashboard.

## Current unique next step

M2.2: implement a deterministic sequential runner based on `mbpp_selected_groups.json`, so two groups of five tasks form continuous sequences while retaining the existing mock Agents and without a real LLM.

## Dataset import progress (2026-07-11)

- The authorized local MBPP-Sanitized source was downloaded from Google Research. The offline importer converted 427 of 427 records into ignored local JSONL output with zero import errors.
- `datasets/manifests/mbpp_candidate_list.json` contains 427 candidate records and two deterministic five-task recommendations. It includes only agent-visible static metadata and is explicitly pending human review.
- The authorized local HumanEval+ v0.1.10 release was downloaded from EvalPlus. The local importer converted 164 of 164 records into ignored local JSONL output with zero import errors.
- The original downloaded files and generated processed task JSONL files remain Git-ignored. No official test or input field appears in the MBPP candidate manifest.
- Human review rejected the tag-only recommendations and approved two fixed groups of five tasks, ten tasks total. The ordered IDs, expected functions, rationale, and reusable knowledge are recorded in `datasets/manifests/mbpp_selected_groups.json` without hidden-test data.
- M2.1 Windows acceptance: selection-manifest tests `3 passed`, importer tests `6 passed`, and full repository tests `18 passed`. openEuler 24.03-LTS-SP3 / Python 3.11.6 reproduced the same `3 passed`, `6 passed`, and `18 passed` results; `git diff --check` passed. Log: `/home/oa/LiteTest-MAS/runs/validation/m2_1_openeuler-20260711-102118.log`.

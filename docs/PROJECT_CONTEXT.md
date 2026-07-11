# Project Context

## Goal

LiteTest-MAS is a low-overhead multi-agent system for test-generation tasks. Its final experiment compares natural-language communication, a structured protocol, non-text StateVector transfer, and cross-task SharedMemory while retaining task effectiveness.

The completed system must coordinate at least three roles spanning planning, retrieval, test generation, execution, and summarization. It must support Text Mode and Protocol Mode, two related task groups of about five tasks, at least ten continuous task runs, the required communication, cost, memory, timing, and test-outcome metrics, and reproducible openEuler 24.03-LTS-SP3 x86_64 execution.

## Current baseline

M1 established a mock/template-based minimal loop. According to the recorded platform validation, A01 completed in Text Mode and Protocol Mode on openEuler with `pytest_returncode` 0, and the repository test result there was `5 passed`. This is a smoke-test baseline, not formal public-dataset evidence.

No real LLM backend, SharedMemory, StateVector, formal HumanEval experiment, coverage/mutation evaluation, Docker/iSulad sandbox, Dashboard, or four-group ablation result exists yet.

## Dataset policy

MBPP-Sanitized is the primary development and experiment dataset. HumanEval is the external-validation dataset after the MBPP workflow is stable. A01 and related hand-authored tasks remain smoke tests only.

For public datasets, reference implementations become `code_under_test`; descriptions, signatures, and entry points may be visible to agents. Official tests are stored only as `hidden_reference_tests` and must never enter agent-visible context. Every imported task retains dataset and original task identifiers.

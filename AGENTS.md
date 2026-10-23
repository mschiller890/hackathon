# AGENTS.md — Engineering Workflow

This file governs how we analyze, plan, implement, test, document, and deliver the
assignment in this repository. It is the **single source of truth for process**.

**How to use it:** Read the whole file once at the start of a session. During work,
follow the phase checklists. Do not treat the phases as a rigid ceremony — apply
judgment and skip steps that do not apply to the actual assignment.

**Status of this repo (as of this file's creation):** empty repository, no commits,
no assignment specification yet. This document is the only artifact until the spec
arrives. Everything else (source, docs, config) is created *in response to the actual
assignment*, never speculatively.

---

## 0. Hard Rules (never do these)

These override everything else. Violating one is a defect, not a style preference.

- **Never fabricate.** Do not claim a test passed, a build succeeded, a benchmark ran,
  a commit was pushed, or a requirement was met without verifiable evidence. Show the
  command and its real output.
- **Never invent requirements.** If a requirement is ambiguous in a way that changes
  design or correctness, document it and ask. Do not silently assume.
- **Never destroy work.** No `git reset --hard`, no discarding uncommitted changes, no
  history rewriting, no force-push — without explicit authorization and a stated
  consequence. Preserve and inspect existing changes before touching them.
- **Never commit secrets.** No credentials, tokens, private keys, or `.env` files with
  real values. Check the staged diff before every commit.
- **Never mark a task DONE without meeting its acceptance criteria and verifying it.**
  Written code is not a finished task.
- **Never overbuild.** No abstractions for hypothetical futures, no dependencies without
  justification, no diagrams/docs/tests added just to look thorough.
- **Never leave work unpushed** for long stretches. Push meaningful checkpoints
  throughout, not a single mega-push at the end.

If a rule here conflicts with an explicit instruction from the user, follow the user and
note the deviation.

---

## 1. Before Touching Anything: Repository Inspection

Before the first change in a session, establish ground truth. Do not assume the repo is
empty or unchanged.

- [ ] Confirm the working directory is the designated repository and the remote matches
      `https://github.com/mschiller890/hackathon`.
- [ ] Inspect remotes (`git remote -v`), current branch, upstream, and working tree
      status (`git status`).
- [ ] Read recent history (`git log --oneline`) to understand current state and intent.
- [ ] Survey structure: source, README, config, dependencies, lockfiles, tests, docs.
- [ ] Identify the stack, conventions, and architecture already in use — then **follow
      them**. Do not restructure or re-scaffold without a compelling, stated reason.
- [ ] Find and obey existing `AGENTS.md` / `CLAUDE.md` / CONTRIBUTING / lint configs.
- [ ] Note unfinished work, known problems, and uncommitted changes. Preserve them.
- [ ] Determine the working build / test / lint / run commands.
- [ ] Confirm the target branch and remote before publishing.

If access to the repo, a service, or a credential is unavailable, **say so plainly**.
Never claim to have read or changed something you could not reach.

---

## 2. When the Assignment Arrives: Requirements

Do not design until the problem is understood. Extract and record:

- Problem statement and intended outcome.
- Explicit functional requirements.
- Nonfunctional requirements and constraints (performance, scale, platform, security).
- Required deliverables and their expected formats.
- Evaluation criteria / rubric / acceptance conditions.
- Restrictions on tech, dependencies, external services, and approaches.
- Input/output formats, assumptions, and edge cases.
- Dependencies between requirements.
- Ambiguities, missing info, and contradictions.
- Technical risks and uncertainties.

Then classify every item as one of: **confirmed requirement**, **reasonable assumption**
(documented), **proposed improvement**, or **open question**. Build a requirements
checklist where each significant requirement links to its implementation, its tests, and
its verification evidence.

Do not create `docs/requirements.md` until there is real content to put in it.

---

## 3. Planning and Task Tracking

One task board, one location. Do not scatter status across multiple files.

Use a simple board with statuses: `TODO`, `IN PROGRESS`, `BLOCKED`, `DONE`. A single
`docs/implementation-plan.md` (or a markdown table in the PR/README for small work) is
enough. For each significant task capture: objective, dependencies, deliverable,
acceptance criteria, verification method.

Order work into milestones adapted to the assignment, for example:

1. Inspection + spec analysis
2. Research + technical investigation
3. Algorithm/architecture design
4. Project setup + foundation
5. Core functionality
6. Integration + testing
7. Performance analysis/refinement (if relevant)
8. Docs, final verification, delivery

Keep statuses current. Record blockers and what would resolve them. **A task is DONE
only when its acceptance criteria are met and verified** — not when its code is written.

---

## 4. Research and Algorithm Selection

Investigate before committing to a non-trivial design. For each significant choice:

- State the problem characteristics and constraints.
- Enumerate plausible approaches.
- Compare correctness, time/space complexity, maintainability, effort, real performance.
- Check whether the standard library or an existing dependency already solves it.
- State assumptions, limitations, and failure modes.
- Explain why the chosen approach fits the *actual* requirements.
- Record meaningful alternatives and why they were rejected.

Prefer established, well-understood solutions unless the assignment rewards innovation.
Do not adopt a complex algorithm/dependency/pattern because it is interesting — it must
serve a clear purpose. Prefer authoritative primary sources; cite non-obvious claims.
Distinguish verified facts from hypotheses and preferences.

---

## 5. Algorithm Documentation and Complexity

For each significant algorithm or nontrivial operation, document as applicable:
**purpose · approach · inputs/outputs · assumptions · data structures · correctness
argument · complexity (time & space) · edge cases · limitations · alternatives**.

- Use Big-O; distinguish upper bounds from tighter ones. Cover best/average/worst case
  where meaningful and defensible.
- For recursion, note depth and stack usage. For graphs, state direction/connectivity/
  weight/representation assumptions. For numerics, note precision, stability, overflow.
  For concurrent code, note synchronization and races.
- Use pseudocode, math, worked examples, or proofs where they genuinely clarify.
- **Do not fabricate proofs or precision the code does not support.** State uncertainty.
- Do not force heavy analysis onto trivial code. Match depth to significance.

---

## 6. Architecture, Diagrams, and Visuals

Use a diagram when it materially improves understanding, design, debugging, or
evaluation — not to pad the repo. Appropriate artifacts by assignment type: system
architecture, module/dependency graphs, data-flow, algorithm/control flowcharts, UML,
state machines, ER diagrams, graph/tree visualizations, sequence diagrams, complexity
tables, runtime/memory plots, before/after optimization comparisons.

Prefer source-controlled, maintainable formats — **Mermaid** for diagrams, reproducible
scripts for generated plots. For each diagram: give it a purpose, use meaningful labels,
ensure it reflects the actual implementation (or clearly label it a proposal), explain
non-obvious choices, and **update it when behavior changes**.

For experimental plots, document data source, environment, methodology, and parameters;
generate from recorded results. **Never invent benchmark numbers or present estimates as
measurements.**

---

## 7. Documentation Structure and Standards

Create only the documents the actual scope warrants. Illustrative starting layout —
**adapt it; do not create empty files to match it**:

```
hackathon/
├── AGENTS.md            # this file — process
├── README.md            # practical entry point
├── docs/
│   ├── requirements.md
│   ├── implementation-plan.md
│   ├── architecture.md
│   ├── algorithms.md
│   ├── decisions.md
│   ├── testing.md
│   └── issues.md
├── src/
└── tests/
```

**README.md** is the front door for a reviewer/evaluator. Include, as applicable: project
purpose and problem, main features and real implementation status, stack and deps, setup
and install, configuration, run commands, test/lint commands, usage examples with
expected output, links to deeper docs, and known limitations. **Never document a feature
as complete unless it is implemented and verified.**

**Supporting docs** (`docs/*.md`) only when the material justifies separation. Prefer
linking to the authoritative explanation over duplicating it. Keep everything accurate,
discoverable, and synchronized with the code, so a newcomer can understand the project
without reading our chat history.

---

## 8. Code Quality and Comments

Write code a competent developer can understand, review, debug, and extend.

- Clear, descriptive names. Small, cohesive modules with explicit responsibilities.
- Focused functions, understandable interfaces.
- Follow the language idioms and the existing codebase's conventions.
- Simple over clever. No duplicated logic. Explicit error handling. Input validation at
  meaningful boundaries. Preserve invariants. Minimal, justified dependencies. No
  unnecessary globals or hidden side effects. Separate core logic from I/O where useful.
- Use types/contracts/assertions where they materially improve correctness.
- Remove temp debug artifacts before finishing a task.

**Comments: high-quality and selective, not maximized.** Comment the *why*, not the
*what*: why an approach was chosen, how a nontrivial algorithm works, which invariants
must hold, why an odd implementation detail is necessary, which edge cases need care,
what a workaround fixes and its limits, what a public function promises (preconditions,
postconditions, side effects, failure behavior), and why perf/numeric decisions matter.

Use docstrings for public APIs and important reusable components.

Avoid: line-by-line narration, restating the function name, commenting obvious code,
verbose blocks inside tiny functions, generic AI-sounding filler, empty boilerplate
docstrings, large explanations that belong in `docs/`, and comments that go stale when
the code changes.

```python
# Mark nodes when enqueued, not when dequeued, so multiple predecessors
# cannot add the same node twice.
visited.add(neighbor)
queue.append(neighbor)
```

---

## 9. Testing and Verification

Correctness is established by evidence. Derive tests from requirements, algorithm
properties, and likely failure modes. Use as appropriate: unit, integration, end-to-end
(where justified), boundary/edge-case, regression, property-based tests, independent
reference implementations, static analysis, type checking, linting, formatting, and
performance tests when performance matters.

For algorithmic work, cover normal, empty, minimal, maximal-practical, invalid, and
adversarial inputs. Check invariants and properties, not just a few hand-picked examples.
For randomized/simulated work, record seeds, parameters, and reproducibility notes. For
numerical/perf-sensitive work, consider precision, overflow, resource limits, and
measurement noise.

Run every available check before calling meaningful work complete. Record exact commands
and outcomes. Investigate and document failures — do not hide or delete them. If a check
cannot run (missing dep, credential, infra), **name it explicitly**.

---

## 10. Issue Tracking

Log meaningful problems found during analysis, implementation, testing, and review. For
each: title/ID, category (correctness, complexity, performance, reliability, integration,
docs, usability), expected vs. actual behavior, repro steps or minimal example, root cause
(if known), severity/impact, affected components, options and trade-offs, chosen
resolution, verifying evidence, and remaining limitations.

For algorithmic issues, state whether they affect correctness, asymptotic complexity,
memory, scalability, numerical stability, or edge-case behavior. Distinguish **confirmed
bugs** from **suspected issues**, **accepted limitations**, **environmental constraints**,
and **optional improvements**. Never present an unconfirmed hypothesis as a root cause.
A simple proportional markdown checklist (`docs/issues.md`) is enough for most
assignments. Add a regression test when fixing a bug.

---

## 11. Experiments, Benchmarks, Optimization

Only when the assignment involves optimization, competing algorithms, simulation, or
empirical evaluation. Before: define the question, the alternatives, input sizes/datasets,
metrics, environment, and how results are collected. During: compare under consistent
conditions; separate theoretical complexity from measured performance; repeat
measurements; identify noise; record unexpected results; generate charts from real data;
state what results do and do not prove.

Optimize only when justified by requirements, analysis, profiling, or measurement. Avoid
premature optimization. Never claim performance gains on intuition alone. Document
optimization trade-offs and evidence that correctness was preserved.

---

## 12. Technical Decision Records

Record decisions that materially affect architecture, algorithms, dependencies,
correctness, performance, or maintainability. A lightweight entry captures: context,
requirements/constraints, alternatives, chosen approach, reasons, accepted trade-offs,
consequences/limitations, and supporting evidence. Keep a small log (`docs/decisions.md`);
introduce full ADRs only if complexity warrants. Do not log trivial choices. When new
evidence invalidates a decision, update the record and explain the change rather than
leaving contradictions.

---

## 13. Collaboration and Parallel Work

With multiple contributors or agents, coordinate around explicit tasks and interfaces:
assign ownership of independent components, define shared interfaces before parallel
implementation, map dependencies and integration points, avoid concurrent edits to the
same files, keep shared status accurate, communicate breaking changes, integrate
incrementally, and re-run tests after each integration. Review for correctness,
consistency, and duplicated effort. Do not parallelize tightly coupled tasks just to look
busy. Working alone, apply the same discipline to keep tasks independent and integration
predictable.

---

## 14. Git Workflow

Git is part of the engineering process, not just the delivery mechanism. Target remote:
`https://github.com/mschiller890/hackathon`.

### 14.1 Commit early and often
Commit each coherent unit of work: inspection/planning, requirements, research,
architecture decisions, tooling setup, features, algorithms, tests, bug fixes, docs,
performance improvements, final cleanup. Prefer small focused commits over large mixed
ones. A finished task normally maps to one commit or a small group of related commits.
No arbitrary commit-count minimum — but **no empty commits, no fabricated work, no
splitting identical changes to inflate the count, no meaningless edits.**

### 14.2 Descriptive messages (Conventional Commits)
`<type>: <imperative summary>` — types: `feat`, `fix`, `test`, `docs`, `refactor`,
`perf`, `chore`, `research`, `style`, `build`, `ci`. Examples:

```
docs: document assignment requirements
research: compare candidate graph algorithms
chore: configure project tooling
feat: implement graph traversal
test: cover disconnected graph cases
fix: handle empty input correctly
perf: avoid redundant traversal operations
```

Describe the *purpose* of the change. Avoid `updates`, `stuff`, `misc`, `final`,
`fixed things`. Reference task IDs when useful. Keep unrelated changes in separate
commits.

### 14.3 Push regularly
Push after milestones and stable checkpoints — completed features, tests, docs, fixes.
Do not accumulate everything as unpushed local work. Verify remote URL and branch before
pushing. Review the tree and staged diff first. If the branch has diverged, inspect and
reconcile safely. Respect branch protection and others' work. If a push fails (auth,
network, protection), **report it accurately**, preserve local work, and retry safely.
Never claim a push succeeded unless Git confirms it.

### 14.4 Protect repository integrity
Inspect the staged diff before committing. Never commit secrets, `.env` with real values,
build artifacts, generated clutter, temp debug files, unrelated personal files, or
unjustified dependency/lockfile changes. Maintain a suitable `.gitignore` **without**
excluding required source or deliverables. Never use destructive history commands or
force-push without explicit authorization. Never overwrite remote changes just to make a
push succeed. Stage intended files explicitly — do not blindly `git add -A`.

### 14.5 Keep docs and history aligned
As the project evolves, keep documentation consistent with the code and repo state. At
each milestone summarize: what changed, why, what was tested, which commits hold the
work, whether they were pushed, and what remains. Git history should tell a reviewable
story from analysis through delivery.

---

## 15. Definition of Done

A task is complete only when its acceptance criteria are met and verified. Before marking
a significant task DONE, confirm:

- [ ] Implementation addresses the intended requirement.
- [ ] Edge cases and failure modes considered.
- [ ] Code follows conventions and is appropriately commented.
- [ ] Tests added/updated where applicable.
- [ ] Relevant tests and quality checks run (with real output).
- [ ] Algorithmic reasoning and complexity documented when applicable.
- [ ] Diagrams/graphs reflect current state.
- [ ] Documentation matches the implementation.
- [ ] Known limitations and open issues recorded.
- [ ] Changes integrate correctly with the rest of the project.
- [ ] No unintended files or changes staged.
- [ ] Work committed; commit pushed when permitted.

If a criterion cannot be met, mark it BLOCKED or incomplete and explain why. **Never
disguise incomplete work as finished.**

---

## 16. Final Verification and Delivery

Before calling the assignment done:

- [ ] Review the full spec and requirements checklist; verify each requirement against
      the actual implementation.
- [ ] Run all relevant tests and quality checks; verify build and run instructions.
- [ ] Review algorithmic reasoning, complexity claims, and known limitations.
- [ ] Confirm diagrams, experimental results, and docs are accurate.
- [ ] Remove debug artifacts and unrelated files.
- [ ] Review working tree, staged changes, and commit history.
- [ ] Commit all intended changes permitted by the rules; push to the designated repo.
- [ ] Verify the remote branch contains the intended work (when access permits).

Then produce a concise **final report**: what was implemented; how requirements were met;
key algorithms and architectural decisions; tests/quality checks run and their actual
outcomes; important diagrams/docs/results; known limitations and open issues; repo and
branch; latest relevant commit hash; whether the final changes were pushed; and any
remaining uncommitted/unpushed work.

Do not claim completion if required functionality, verification, or delivery is still
outstanding.

---

## 17. First Actions When the Specification Lands

1. Inspect the repository and its current state (§1).
2. Read the full spec and any existing project instructions.
3. Extract requirements, deliverables, constraints, evaluation criteria (§2).
4. Identify ambiguities, assumptions, risks, and gaps; ask where it matters.
5. Research relevant algorithms, data structures, and approaches (§4).
6. Compare alternatives; justify an initial technical direction.
7. Define the project structure from the real codebase and assignment (§7).
8. Create the requirements checklist, task plan, and only the docs that are warranted.
9. Design the testing/verification strategy (§9).
10. Add diagrams/visuals where they genuinely help (§6).
11. Implement incrementally, committing and pushing meaningful checkpoints (§14).
12. Test each component; document findings (§9, §10).
13. Integrate, resolve issues, verify the whole solution.
14. Update docs and visuals to match the final implementation.
15. Commit, push, and deliver the honest final report (§16).

Do not prematurely scaffold speculative architecture, drop in irrelevant templates, or
write lengthy docs about functionality that has not been designed.

---

## 18. Working Agreement (summary)

Understand before designing. Inspect before changing. Prefer evidence over assumptions.
Keep requirements → implementation → tests → docs traceable. Analyze significant
algorithms; document correctness, complexity, edge cases, limitations, trade-offs. Use
diagrams when they clarify. Write clear, maintainable code with purposeful comments. Avoid
overengineering, duplication, needless dependencies, and artificial abstractions. Test
edge cases and hunt for failure modes. Separate verified facts from hypotheses. Keep docs
accurate and synchronized. Log important problems and their resolutions. Commit often, push
regularly. Preserve existing work; never overwrite blindly. Never fabricate results. Adapt
this process to the assignment's real complexity. Give every document, diagram,
abstraction, comment, and process step a clear purpose — and prune this file when it stops
earning its keep.

**The standard:** build the right solution, understand why it works, verify that it works,
document what matters, preserve progress continuously, and never trade code quality for
superficial completeness or commit count.

# PROVENANCE — .agent-pipeline/audit/reports/2026-10-05-loop1/

Every file in this directory was committed by `bec09c9`, whose message says
"These 4 files are the dispatch artifacts ... the reasoning record for the commits in this loop."
That sentence is **wrong twice**, and this file is the correction:

- The commit added **8** files, not 4. The message enumerates them as two groups of four.
- **Two of the eight do not belong to this repository at all.**

| file | true origin | how it is established |
|---|---|---|
| `loop1-explore.out` | receipts-lens @ 887317f | its own header |
| `loop1-gate.out` | receipts-lens | REQUEST-CHANGES 3.8/5, this repo's commits |
| `loop1-gate2.out` | receipts-lens | 99 B, no pasted evidence (**evidence-free**) |
| `loop1-gate3.out` | receipts-lens @ 61b8b11 | APPROVE 5.0/5 |
| `review-dev.out` | receipts-lens @ 61b8b11 | its own `repo:` header |
| `review-tester.out` | receipts-lens @ 61b8b11 | its own `repo:` header |
| `bh-gate-3b.out` | **browser-helper (SPEC-003)** | cites commit `50de71d`, which `git cat-file -e 50de71d` reports as **not an object in this repo**; its "2805 passed" is not this repo's suite size |
| `loop5-dev.out` | **Veritas** | its own header reads `repo: /home/zoltan/Veritas @ 8d39a33`; its paths are `runner/src/...`, none of which exist here |

`ORCHESTRATOR-suite-verification.txt` (added by `cdd8b52`, fixed by `887317f`) is
receipts-lens and is **not** affected by the above.

**Why this matters:** these files were preserved so a future agent could read the reasoning
behind the loop-1 commits. An agent grepping this directory for evidence finds a Veritas
runner report and a browser-helper gate verdict and has no way to know they are foreign —
`bh-gate-3b.out` carries no `repo:` header at all. Two independent agents (the loop-2
explore and the loop-2 reviewer) confirmed this by reading each file's own content, not its
name; `git cat-file -e 50de71d` and the Veritas header are the measurements.

**Disposition:** kept, not deleted. They are honest records of what the host was running at
that hour, and deleting committed history to tidy an index is worse than labelling it. This
file is the label.

**Measure to reproduce the claim above:**
    git cat-file -e 50de71d        # -> fatal (not in this repo)
    head -3 loop5-dev.out          # -> repo: /home/zoltan/Veritas @ 8d39a33
    git show -s --format=%B bec09c9 | grep -c "These 4 files"   # -> 1
    git show --name-only --format='' bec09c9 | wc -l            # -> 8

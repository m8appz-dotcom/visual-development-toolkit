# Reviewed delivery

The delivery unit is a real problem with acceptance evidence: issue → focused branch and commits → PR → checks and review → merge → verification. [Workflow improvement issue #1](https://github.com/m8appz-dotcom/visual-development-toolkit/issues/1) records the initial adoption.

## Roles and provenance

[Kenneth Yepez](https://github.com/kennethyepez) directs requirements, architecture, integration, validation, and delivery. AI coding agents implement changes under that direction. The repository is hosted by [M8 Apps](https://github.com/m8appz-dotcom). Human and automated review are identified by their actual records; an AI review is not represented as a human peer approval.

Historical imports retain labels such as M8 Apps, Titan, or local workstation authors where they appear in Git. They are source provenance, not new claims of individual authorship. Do not reassign old commits, dates, or emails to improve a contribution graph. Use the actual participant's configured identity for new work and preserve upstream authorship and licenses.

## Commit boundaries

- Formatting policy and any line-ending normalization form a separate change. Binary originals remain byte-identical.
- A refactor should preserve behavior and include relevant regression checks.
- Behavioral changes explain their trigger, resulting behavior, and verification.
- Examples and measured results state their inputs and whether providers or customers were involved.

## Before integration

The default branch requires a PR, the existing CI jobs, a source-format check, and the `review/ai` status once the gate is installed. Branch deletion and force-push are disallowed. Existing recovery branches remain untouched.

The review gate runs trusted base-branch code on PR metadata and comments. It never checks out or executes the PR head with its write-scoped token. It accepts only the configured Codex bot and app IDs, parses review metadata as data, requires the exact head SHA, and rejects unresolved findings. A configured security review must finish for that same revision. Unknown or missing results remain pending. This is an automated review result, not a production security certification.

The first adoption PR is checked and reviewed before the gate exists on the default branch; branch rules are enabled after that reviewed bootstrap. Subsequent deliveries use the installed gate. A workflow-dispatch recheck can evaluate an open PR without requesting another paid review. Do not manufacture comments or bypass the gate to make a merge look reviewed.

If another person reviews a change, record their real review. Requiring a human approval is appropriate only when an actual authorized reviewer is available. Account aliases and agents are not counted as additional people.

## Verification and rollback

Use the checks documented in the README and CI. Record real commands and outcomes in the PR. Keep fixtures, live-provider evaluations, and customer outcomes distinct. Revert a focused merged change with a new commit/PR when needed; do not force-push history or delete recovery refs.

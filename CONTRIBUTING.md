# Contributing

Start with the [README](README.md), [walkthrough](docs/DEMO.md), and [delivery workflow](docs/DELIVERY.md). Use an isolated checkout and documented runtimes. Do not connect tests to production data or services.

1. Define a real issue with an observable acceptance criterion. The workflow improvements are tracked in [#1](https://github.com/m8appz-dotcom/visual-development-toolkit/issues/1).
2. Create a branch for that purpose. Keep normalization, refactoring, behavior changes, and documentation in separate commits when they need separate review or rollback. Follow `.editorconfig` and `.gitattributes`.
3. Open a PR linking the issue. Explain the result, alternatives where useful, verification, material limitations, and recovery.
4. Let the current-revision CI and identified review finish before merging. Address findings and rerun the affected checks. Human reviewers are credited only when they actually review; automated review is labeled AI.
5. Verify the merged revision and close the issue against its acceptance evidence. Keep recovery refs and original assets.

The main branch is intended to require PRs and its actual CI checks. The trusted review gate reports `review/ai` from the configured Codex bot's metadata for the exact PR head; see [delivery details](docs/DELIVERY.md). A maintained solo project does not invent a second human approval to satisfy a checklist.

Use authored fixtures for offline checks. Do not submit credentials, private conversations, customer data, downloaded runtimes, or generated caches. Preserve [source-use terms](LICENSE.md), upstream notices, and [security reporting](SECURITY.md). Paid providers and active infrastructure require an agreed scope.

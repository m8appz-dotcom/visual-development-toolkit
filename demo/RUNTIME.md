# Shared demo runtime 1.1.2

The canonical runtime lives in [Visual Development Toolkit](https://github.com/m8appz-dotcom/visual-development-toolkit/tree/050af024fccfab29929759bd6d9be28296b733a8/demo). `runtime-lock.json` pins that exact commit and every file's SHA-256. Each repository includes a checked local copy so it runs without another checkout or a network import. Product styles, examples, adapters and state remain local.

`npm run check` rejects drift. Verify explicitly with `node sync-runtime.mjs --check`. Restore the pinned bytes from a trusted local Toolkit checkout using `node sync-runtime.mjs --from /path/to/toolkit/demo`; the command verifies all members before writing any, rejects linked/outside files, and never downloads or runs remote code.

For an upgrade, make and test the common change in Toolkit, publish its focused source commit through a PR, then update the lock's version/source/checksums and synchronize consumers in their own reviewed PRs. Keep security fixes together with their regression evidence. Do not bypass the drift check by changing a hash for a local patch. Bump this runtime's version when behavior changes.

The shared server denies microphone access by default. Only M8's server-owned engine adapter opts into self microphone access. This option cannot be chosen by a browser request. Passkey/session/origin gates are unchanged. No inference credentials or production data belong in this runtime.

Version 1.1.0 adds an explicit HTTPS hosting contract, exact-host RP IDs and bounded saved task storage. Local launchers remain localhost-only. Hosted consumers must provide private external state and complete holder acceptance; see HOSTING.md where available.

Version 1.1.1 bounds request depth and complexity before execution and commits workspace/credential changes only after candidate serialization and atomic persistence succeed. A rejected nested request or failed write preserves other users' in-memory and saved work.

Version 1.1.2 checks serialized UTF-8 byte budgets before whole-store serialization: 192 KiB per slot, 384 KiB per user, 4 MiB of workspace state, 30,000 nodes per user and 100,000 nodes globally, 8 KiB per access record and 1 MiB of access metadata. Existing store files above 8 MiB fail closed without rewriting them. Credential transports retain only unique recognized WebAuthn values. At capacity, rejected growth preserves saved work and replacing a slot with smaller data remains possible. Export local copies before removing or migrating saved content.

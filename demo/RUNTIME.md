# Shared demo runtime 1.1.0

The canonical runtime lives in [Visual Development Toolkit](https://github.com/m8appz-dotcom/visual-development-toolkit/tree/cb91730c1b74e849609896d623d726a5b5ce5b78/demo). `runtime-lock.json` pins that exact commit and every file's SHA-256. Each repository includes a checked local copy so it runs without another checkout or a network import. Product styles, examples, adapters and state remain local.

`npm run check` rejects drift. Verify explicitly with `node sync-runtime.mjs --check`. Restore the pinned bytes from a trusted local Toolkit checkout using `node sync-runtime.mjs --from /path/to/toolkit/demo`; the command verifies all members before writing any, rejects linked/outside files, and never downloads or runs remote code.

For an upgrade, make and test the common change in Toolkit, publish its focused source commit through a PR, then update the lock's version/source/checksums and synchronize consumers in their own reviewed PRs. Keep security fixes together with their regression evidence. Do not bypass the drift check by changing a hash for a local patch. Bump this runtime's version when behavior changes.

The shared server denies microphone access by default. Only M8's server-owned engine adapter opts into self microphone access. This option cannot be chosen by a browser request. Passkey/session/origin gates are unchanged. No inference credentials or production data belong in this runtime.

Version 1.1.0 adds an explicit HTTPS hosting contract, exact-host RP IDs and bounded saved task storage. Local launchers remain localhost-only. Hosted consumers must provide private external state and complete holder acceptance; see HOSTING.md where available.

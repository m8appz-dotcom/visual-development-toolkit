# Visual Development Toolkit — interactive English demo

Search, filter or sort the sixteen English collection files. Inspect an original, select files, and compare their SHA-256 with the included manifest. Export a standard ZIP containing the original bytes and a package manifest. Changed files stop packaging.

See [ENGINES.md](ENGINES.md) for the actual engine connection, additional runtime setup, credentials and acceptance limits.

## Run locally

Requires Node.js 22 or newer and npm. From the repository root:

```sh
cd demo
npm ci --ignore-scripts
npm run check
npm start
```

Open **http://localhost:8875/**. The server binds only to 127.0.0.1. If another app uses this port, choose an unused port with the PORT environment variable; do not stop that app. Use the same localhost origin for subsequent passkey access. Stop this demo with Ctrl+C.

## Try the full example

1. Search, filter or sort the sixteen English collection files.
2. Inspect an original, select files, and compare their SHA-256 with the included manifest.
3. Export a standard ZIP containing the original bytes and a package manifest. Changed files stop packaging.

All UI labels, accessibility text, demo conversation/script content and new exports are in English. English adaptations are separate fixtures; historical source examples remain unchanged. User-entered text retains the language the user types.

## Local work and private access

Guest exploration saves drafts in this browser's local storage. It does not require a model account. Use **Private workspace → Export workspace** for a recoverable JSON copy; restore a compatible export and undo that restore if needed. Local browser storage is not a secure vault. Use authored examples, not confidential records.

The included server integrates FIDO2/WebAuthn for optional private workspace copies. It stores public credential material and workspace JSON in ignored **.demo-state/workspaces.json**, outside the static directory. It never receives a PIN, fingerprint or private key. Registration and login require user verification; the server validates the RP ID and origin, consumes challenges once, and uses HttpOnly/Secure/SameSite sessions. Add a second passkey after signing in and keep an exported workspace copy.

**The holder must still complete real registration, sign-in, second-passkey access and recovery acceptance.** Automated negative checks do not substitute for that physical interaction. No existing authentication or production access was removed.

## Boundaries

The included fixtures are imported, verified and packaged through the actual MCP stdio gateway in isolated folders. No native creative application or Docker container is started.

The local server supports its documented localhost origin. This change does not deploy a public service or make these local workspaces production-ready. A public deployment needs a stable HTTPS origin/RP ID, durable protected storage, retention policy and completed holder acceptance. No provider keys or production data are included. No Spark data or services are touched.

## Verification

See [VERIFY.md](VERIFY.md) for the browser journeys actually exercised and remaining limits. `npm run check` verifies the standalone server, protected workspace endpoints, single-use challenges, immutable assets, module syntax and dependency audit. The browser inspection is a separate recorded acceptance step.

To remove this isolated demo, revert its feature commit; the original application and historical examples remain independent.

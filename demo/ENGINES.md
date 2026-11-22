# Repository engine connection

**Verify originals / Export package**

Calls the actual FastMCP stdio gateway: create_project, import_target, verify_originals and package_project. Selected paths must be in the committed collection manifest. Every input and archive member is checked against its SHA-256. Source files are copied byte-for-byte; no image transformation occurs.

## Setup

Use Python 3.12 or newer with the repository development requirements installed in an isolated environment (`python -m pip install -r requirements-dev.txt`). The native gateway uses `Path.is_junction()` and `hashlib.file_digest()`; Python 3.10 and 3.11 cannot run this connected demo. Set `DEMO_PYTHON` to that executable. Each run supplies its own MODDING_LAB_ROOT; it never uses the native lab default. This portable workflow starts no Docker containers or native editor applications.

Run the demo with `npm start` from this directory and open its documented localhost origin. The static directory is `public`; configuration, adapters and private run folders are never served as static files.

## Access and outputs

The existing FIDO2/WebAuthn workspace flow remains in place. Real holder registration, sign-in and second-key recovery still require holder interaction. Live provider actions require a verified session. There is no demo authentication bypass.

Machine-only acceptance can use an explicitly configured DEMO_SERVICE_TOKEN of at least 32 random bytes. Keep it in a private server environment and never in browser code or URLs. It represents a service identity, not a human passkey test. No token is included in this repository.

Each engine task writes only beneath its own ignored `.demo-state/engine/<run>` directory. Download links require the same browser ownership cookie (or the configured service identity). Jobs expire after one hour in memory; disk files are retained locally for recovery and are not automatically deleted. No production database or existing service is changed. Stop this local demo normally when finished.

The gateway rejects foreign origins, unknown actions, oversized input, cross-session artifact access and outputs outside the job directory. Raw provider errors stay in private run logs. It never accepts an arbitrary remote URL or a filesystem path from the browser.

## Acceptance

The adapter is exercised separately from its browser journey; see VERIFY.md. `npm test` includes origin, access, job ownership and error-isolation checks. Physical passkey and live-provider limits are stated explicitly. Preserve `.demo-state` before removing or replacing this isolated demo if its outputs matter.

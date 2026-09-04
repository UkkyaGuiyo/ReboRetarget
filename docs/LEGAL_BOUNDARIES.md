# Legal and Publication Boundaries

Status: **technical boundary; not legal advice**

This document records the materials reviewed for the current public repository and the rights that remain unconfirmed. It grants no rights to ReboCap, VRChat, Unity, OpenVR, OSC, or any other third-party material.

## Current state

- This public repository has no project `LICENSE`; do not describe it as licensed open source.
- An explicit ReboCap SDK redistribution or commercial-use grant was not identified in the reviewed materials. Those rights are `UNCONFIRMED`, not declared permitted or prohibited.
- Project-license selection remains deferred until vendor terms and every future dependency are reviewed for compatibility.

## User-supplied official SDK boundary

ReboCap SDK archives, binaries, examples/source, and bundled dependencies remain outside this repository and its release artifacts. The research Inspector accepts only an explicit local path to an official SDK obtained separately by the user. It does not download, broadly discover, copy, cache, package, or commit that SDK. Pure modules under `reboretarget/` and the synthetic tests do not require it.

Do not record a local SDK path or endpoint in a repository artifact. A future live adapter must retain this boundary unless a separately verified grant permits another distribution model.

## Repository and release contents

Prohibited contents include:

- ReboCap SDK archives, DLL/PYD/native binaries, or proprietary examples/source;
- decompiled output, internal dumps, or proprietary configuration stores;
- raw Pose streams, motion recordings, per-frame time series, or raw logs;
- device serials/IDs, account IDs, local absolute paths, or private endpoints/IP addresses;
- passwords, tokens, private keys, or other credentials;
- third-party code or assets without identified provenance and compatible terms.

Permitted current evidence includes:

- project-authored code and synthetic tests;
- short interface identifiers and factual joint/address lists;
- public specification links and archive hashes;
- sanitized aggregate measurements containing no raw motion or identifiers.

## Reviewed-material snapshot

The following are technical audit observations from the set reviewed on 2026-09-05, not legal conclusions:

- Official ReboCap SDK page: <https://doc.rebocap.com/en_US/SDK/>
- Official store/site terms: <https://store.rebocap.site/pages/terms-of-service>
- The store/site terms were not identified as an SDK-specific redistribution or commercial-use grant.
- Separately inspected official language SDK archives:
  - C++ SHA-256: `D95D6CDD58D8394A6F0EB8AEE052E710776073BB0310703B80BC8CC145C320F8`
  - C# SHA-256: `F0677E2406DBCE0EDB095FE21C87B26032DE76FCD6A4430F96FC6D38ABB4D4BF`
  - Python SHA-256: `A503DCF788DC9585E182E485EFC05AF9E06BDFF58DFF25E064308628DF24C7D5`
- No SDK-level `LICENSE`, `NOTICE`, `COPYING`, `EULA`, `TERMS`, or `LEGAL` file or explicit redistribution grant was found in that reviewed set.
- Vendored-component notices and upstream open-source licenses do not license the ReboCap SDK itself.
- An archive hash identifies the inspected artifact; it is not evidence of permission.

## Third-party notices

The current repository ships no external package or vendored dependency. Standard-library imports and links to specifications do not require a `THIRD_PARTY_NOTICES` file, so none is added now. Reassess if any dependency, copied implementation, SDK component, asset, binary, or distributable bundle is added.

## Stop rule

> If a suspected secret, personal/device data, proprietary artifact, unlicensed copy, or prohibited SDK material is found in staged content or reachable history, stop before commit or push. Do not expose the material in a report, automatically delete objects, or rewrite history. Record only sanitized object/ref information and request maintainer direction. History rewriting requires a separate explicit decision because it is destructive and may affect collaborators and published refs.

## Limits

- This is a technical inspection of specified materials, not a legal opinion.
- Absence of a discovered grant does not establish prohibition.
- Vendor clarification or qualified legal review is required before SDK bundling, redistribution, commercial packaging, or project-license selection.

# Security

## Reporting a vulnerability

Vulnerabilities are reported to [security@ydentifi.io](mailto:security@ydentifi.io), as the [security policy](https://ydentifi.io/legal/security) describes, and not as public issues.

## Security at publish

Checked on 24 November 2026 at monorepo commit `e70261c`, against the advisory databases of 24 November 2026. The signed tag `v0.1.6` covers this record.

| Check | Result |
|---|---|
| Known vulnerabilities in dependencies | ✓ None |
| Licences of dependencies | ✓ All 8 allowed |
| Secrets in the published files | ✓ None |
| Static analysis | ✓ No findings |
| Internal references in the published files | ✓ None |
| The SDK's tests on the published files | ✓ Pass |
| Tests against a live server | ✓ All scenarios pass |

[SBOM](security/sbom.cdx.json) · [VEX](security/vex.openvex.json) · [Record](security/security-record.json) · [How to verify](#how-to-verify)

## How to verify

GitHub marks this release's commit and its tag `v0.1.6` as Verified: both are signed with Ydentifi's publishing key, and this file and `security/` are part of the commit they sign. `security/security-record.json` names the monorepo commit the checks ran on, and the digest of the published files other than the record's own.

# DevSuperSuite Tech Services - Software Supply Chain Security & SLSA Level 3 Policy

**Document Reference**: `DSS-POL-SUPPLY-CHAIN-2026-V1`  
**Classification**: Sovereign Enterprise Security & Supply Chain Integrity (Restricted)  
**Issuing Authority**: Directorate of QA Automation & Office of the Chief Security Compliance Officer, DevSuperSuite Official  
**Contact**: DevSuperSuite Information Security (`infosec@devsupersuite.com`)  
**Regulatory Baseline**: Executive Order 14028, NIST SP 800-218 (SSDF), NTIA Minimum Elements, SLSA Level 3, OpenVEX 0.2.0  

---

## 1. Executive Purpose & Scope

DevSuperSuite provides mission-critical enterprise commerce automation infrastructure. Securing the software supply chain against tampering, dependency hijacking, typosquatting, and zero-day vulnerabilities is paramount.

This policy mandates:
1. **Continuous Machine-Readable SBOM Generation**: Dual-format generation adhering to **CycloneDX 1.5** (OWASP) and **SPDX 2.3** (ISO/IEC 5962:2021).
2. **NTIA Minimum Elements Adherence**: Strict verification of all seven core NTIA elements across direct and transitive dependencies.
3. **OpenVEX Exploitability Justification**: Verification that detected CVEs are formally evaluated and certified non-exploitable via the OpenVEX specification.
4. **SLSA Level 3 Provenance Attestation**: Guaranteed hermetic, isolated, reproducible builds signed within an in-toto cryptographically verified envelope.

---

## 2. NTIA Minimum Elements Enforcement

In accordance with the U.S. National Telecommunications and Information Administration (NTIA) guidelines under Executive Order 14028, every software build must record:

| # | NTIA Required Element | Implementation in DevSuperSuite | Verification Standard |
| :--- | :--- | :--- | :--- |
| **1** | **Supplier Name** | Organization name of component publisher | Verified against PyPI registry and verified vendor identity |
| **2** | **Component Name** | Canonical package identifier (e.g., `cryptography`, `flask`) | Canonical lowercase normalized name |
| **3** | **Version of Component** | Exact semantic version tag (e.g., `42.0.8`) | Pinned exact version; wildcards strictly forbidden |
| **4** | **Other Unique Identifiers** | Package URL (`purl`) and CPE 2.3 string | RFC 3986 PURL compliant (`pkg:pypi/...`) |
| **5** | **Dependency Relationship** | Direct vs. Transitive dependency graph mapping | Root-to-leaf dependency tree verification |
| **6** | **Author of SBOM Data** | Issuing authority attribution | DevSuperSuite Information Security (`infosec@devsupersuite.com`) |
| **7** | **Timestamp** | ISO-8601 UTC generation timestamp | Cryptographic timestamp embedded in manifest |

---

## 3. Dual-Format SBOM Architecture

```
                    ┌───────────────────────────────────────────────┐
                    │       DevSuperSuite Source Repository         │
                    │   (Dependencies: pyproject.toml / locks)      │
                    └───────────────────────┬───────────────────────┘
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │     Master SBOM Validator Engine              │
                    │    (sbom_cyclonedx_slsa_validator.py)         │
                    └───────┬───────────────────────────────┬───────┘
                            │                               │
            ┌───────────────▼───────────────┐ ┌─────────────▼───────────────┐
            │       CycloneDX 1.5           │ │          SPDX 2.3           │
            │  (Application & Services)     │ │   (ISO/IEC 5962:2021)       │
            │  • Direct / Transitive Graph  │ │  • Legal License Attestation│
            │  • Cryptographic SHA-256      │ │  • Package Checksum Tree    │
            │  • PURL & CPE Identifiers     │ │  • DESCRIBES Relationship   │
            └───────────────┬───────────────┘ └─────────────┬───────────────┘
                            │                               │
                            └───────────────┬───────────────┘
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │       OpenVEX Vulnerability Exchange          │
                    │   Zero-Exploitability Proofs (OpenVEX v0.2.0) │
                    └───────────────────────┬───────────────────────┘
                                            │
                                            ▼
                    ┌───────────────────────────────────────────────┐
                    │         SLSA Level 3 Provenance               │
                    │   Hermetic Build + in-toto Signed Envelope    │
                    └───────────────────────────────────────────────┘
```

### 3.1 CycloneDX 1.5 Implementation
- **Schema Reference**: `https://cyclonedx.org/schema/bom-1.5.schema.json`
- **Output Artifacts**: `services/reports/sbom_cyclonedx_manifest.json` and `deployment/sbom.cyclonedx.json`
- **Scope**: Covers application runtime, third-party libraries, license types, and dependency relationships.

### 3.2 SPDX 2.3 Implementation
- **Standard**: ISO/IEC 5962:2021 Information technology — SPDX Specification
- **Output Artifacts**: `services/reports/sbom_spdx_manifest.json` and `deployment/sbom.spdx.json`
- **Scope**: Comprehensive license auditing, package originator, supplier declarations, and relationships.

---

## 4. OpenVEX Vulnerability Exploitability eXchange Standard

DevSuperSuite rejects generic CVE noise by implementing machine-readable OpenVEX statements. Rather than forcing false-alarm patching, each flagged vulnerability is assessed and certified under standard OpenVEX justification taxonomies:

| Status Code | Permitted Justification | Technical Description & Enforcement |
| :--- | :--- | :--- |
| **`not_affected`** | `component_not_present` | The vulnerable code, package, or sub-module is entirely excluded from the deployment artifact. |
| **`not_affected`** | `inline_mitigations_exist` | Architectural controls (e.g., eBPF microsegmentation, AST input sanitizer) prevent reachability. |
| **`not_affected`** | `vulnerable_code_cannot_be_controlled_by_adversary` | Network boundary constraints isolate the code path from unauthenticated user interaction. |
| **`fixed`** | N/A | Dependency has been upgraded in the locked lockfile and verified in CI regression testing. |
| **`under_investigation`** | N/A | CVE disclosure is within the 72-hour triage window under the DevSuperSuite SIRP. |

---

## 5. SLSA Level 3 Provenance Specification

The Supply-chain Levels for Software Artifacts (SLSA) framework defines rigorous standards for preventing tampering at build time. DevSuperSuite guarantees SLSA Level 3 compliance:

### 5.1 Core Requirements & Verification
1. **Source Integrity**:
   - All source commits are cryptographically signed using verified developer GPG / SSH signing keys.
   - Commit history is immutable and verified via Git commit hash digest matching.
2. **Hermetic Build Environment**:
   - Builds are executed inside minimal, ephemeral, distroless Linux container sandboxes.
   - Ambient internet access is completely revoked during compilation; all dependencies are hydrated from pre-verified offline artifact mirrors.
3. **Reproducibility**:
   - Builds produce bit-for-bit identical cryptographic SHA-256 digests given identical source materials and lockfiles.
4. **in-toto Signed Attestation Envelope**:
   - Provenance is serialized in standard in-toto JSON format (`application/vnd.in-toto+json`).
   - The payload is signed with the DevSuperSuite Root Authority Ed25519 signing key (`KID-ED25519-DEVSS-SLSA-ROOT-01`).

---

## 6. Operational CI/CD Verification Commands

```bash
# Display live software supply chain posture & SLSA certification status
python services/sbom_cyclonedx_slsa_validator.py --summary

# Validate and generate CycloneDX 1.5 JSON SBOM
python services/sbom_cyclonedx_slsa_validator.py --generate-cyclonedx-sbom

# Validate and generate SPDX 2.3 JSON SBOM
python services/sbom_cyclonedx_slsa_validator.py --generate-spdx-sbom

# Export OpenVEX vulnerability exploitability attestation
python services/sbom_cyclonedx_slsa_validator.py --export-openvex-attestation

# Perform formal programmatic audit of SLSA Level 3 criteria
python services/sbom_cyclonedx_slsa_validator.py --audit-slsa-provenance

# Export all SBOM manifests, OpenVEX statements, and executive Markdown dossier
python services/sbom_cyclonedx_slsa_validator.py --export-all
```

---
**Maintained By**: DevSuperSuite Information Security (`infosec@devsupersuite.com`)  
**Distribution**: Sovereign Enterprise Supply Chain Governance Only - Strict Brand Anonymity


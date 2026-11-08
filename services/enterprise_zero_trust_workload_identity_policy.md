# DevSuperSuite Tech Services - Enterprise Zero-Trust Workload Identity Policy

**Document Reference**: `DSS-POL-SPIFFE-ZTNA-2026-V1`  
**Classification**: Sovereign Enterprise Zero-Trust Workload Identity (Restricted)  
**Issuing Authority**: Directorate of QA Automation & Office of the Chief Security Compliance Officer, DevSuperSuite Official  
**Contact**: DevSuperSuite Information Security (`infosec@devsupersuite.com`)  
**Regulatory Frameworks**: SPIFFE (Secure Production Identity Framework for Everyone), SPIRE Runtime, NIST SP 800-207 (Zero Trust Architecture), DoD Zero Trust Strategy, RFC 8446 (TLS 1.3), FIPS 140-3  

---

## 1. Executive Purpose & Zero-Trust Architecture Principles

Traditional perimeter-based network security assumes that network locality implies trust. Under DevSuperSuite's **Zero-Trust Network Architecture (ZTNA)**, network locality provides zero security authorization. Every autonomous agent, microservice, and background daemon must continuously prove its cryptographic identity using **SPIFFE / SPIRE Workload Identity Documents (SVIDs)**.

This policy mandates:
1. **Cryptographic Identity for Every Process**: No workload may communicate across network boundaries without a valid SPIFFE ID.
2. **Ephemeral, Short-Lived Credentials**: SVID certificates must have a maximum lifetime of `< 60 minutes` (default 30 minutes) and renew automatically at 50% lifetime.
3. **Multi-Factor Workload Attestation**: SVID issuance requires combined validation of kernel selectors (cgroups, systemd units, container image SHA-256 digests).
4. **Hardware-Anchored Node Identity**: SPIRE server and agent nodes must anchor their identity to physical hardware (TPM 2.0 endorsement keys or AWS Nitro Enclave attestation quotes).
5. **Cross-Enclave Federation**: Mutual trust federation between commercial, federal (`gov.devsupersuite.io`), and air-gapped sovereign (`scif.devsupersuite.io`) trust domains.

---

## 2. SPIFFE Identity Specification & URI Format

In compliance with the SPIFFE standard specification:
- **Format**: `spiffe://<trust-domain>/<workload-type>/<workload-name>`
- **Example Primary Identifiers**:
  * `spiffe://devsupersuite.io/agent/ast-parser`: Sandboxed AST compilation engine.
  * `spiffe://devsupersuite.io/agent/mcp-daemon`: Sovereign Model Context Protocol background daemon.
  * `spiffe://devsupersuite.io/service/billing-engine`: Commercial ledger and invoicing engine.
  * `spiffe://devsupersuite.io/service/license-verifier`: Hardware-bound license verification service.
  * `spiffe://devsupersuite.io/service/dispute-defense`: Autonomous evidence and dispute defense engine.

```
                    ┌────────────────────────────────────────────────────────┐
                    │               SPIRE Server & Root CA                   │
                    │   Hardware TPM 2.0 / Nitro Enclave Root Authority Key  │
                    └───────────────────────────┬────────────────────────────┘
                                                │
         ┌──────────────────────────────────────┴──────────────────────────────────────┐
         │ (Node Attestation: TPM 2.0 EK)                                              │ (Trust Domain Federation)
         ▼                                                                             ▼
┌─────────────────────────────────┐                                           ┌─────────────────────────────────┐
│          SPIRE Agent            │                                           │   Federated Trust Domain        │
│   (Kernel Workload Attestor)    │                                           │   (gov.devsupersuite.io)        │
└────────────────┬────────────────┘                                           └─────────────────────────────────┘
                 │
                 │ Workload Attestation via Selectors:
                 │ • k8s:ns:agent-commerce
                 │ • container:image:sha256:<digest>
                 │ • unix:uid:1000x
                 ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 Workload Process (e.g. ast-parser)                              │
│  • Ingests X.509 SVID (SAN: spiffe://devsupersuite.io/agent/ast-parser) via SPIFFE Workload API │
│  • Enforces mutual TLS 1.3 (TLS_AES_256_GCM_SHA384) with peer workloads                        │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Workload Attestation State Machine & Selectors

SPIRE agents query local kernel and container runtime interfaces to attest workload identity prior to signing an SVID:

| Selector Namespace | Verification Mechanism | Security Objective |
| :--- | :--- | :--- |
| **`k8s:ns:<namespace>`** | Kubernetes API / cgroup path | Isolates process within the `agent-commerce` namespace. |
| **`k8s:sa:<serviceaccount>`** | Token projection inspection | Binds process to specific RBAC service accounts. |
| **`container:image:sha256:<hash>`** | Container runtime digest matching | Guarantees code authenticity against verified Sigstore Cosign digest. |
| **`systemd:unit:<unit>`** | systemd D-Bus cgroup verification | Confirms process was spawned by authenticated system daemon. |
| **`unix:uid:<uid>`** | OS kernel syscall inspection | Enforces non-root execution (UID $\ge 10000$). |

---

## 4. X.509 SVID & JWT SVID Lifecycle Controls

### 4.1 X.509 SVID Lifetime & Automated Rotation
- **Default TTL**: **1,800 seconds (30 minutes)**.
- **Maximum Ceiling**: **3,600 seconds (60 minutes)**. SVIDs exceeding 3,600s are rejected by policy gates.
- **Automated Rotation**: Workloads must initiate automated rotation when **$\ge 50\%$** of lifetime has elapsed (at 15 minutes).
- **Grace Period**: Workloads maintain dual certificates during the 5-minute handover window to ensure zero connection dropping.

### 4.2 Mutual TLS 1.3 Protocol Requirements
- **Protocol**: Strictly TLS 1.3 (RFC 8446). TLS 1.0, 1.1, and 1.2 handshakes are aborted at the TCP socket layer.
- **Permitted Ciphersuite**: `TLS_AES_256_GCM_SHA384` exclusively.
- **Client Authentication**: Mandatory bidirectional mutual authentication. Server and client must present valid SVIDs.

---

## 5. Multi-Domain Sovereign Trust Federation

DevSuperSuite operates across three sovereign trust domains:
1. **`devsupersuite.io`**: Commercial enterprise SaaS and autonomous commerce cluster.
2. **`gov.devsupersuite.io`**: AWS GovCloud (US) enclave for civilian federal agencies (FedRAMP High).
3. **`scif.devsupersuite.io`**: Air-gapped defense enclaves for classified DoD IL5 workloads.

Federation bundles are cryptographically signed by root authorities and synchronized over HTTPS endpoints (`/.well-known/spiffe-bundle`) with SPIFFE Trust Domain Federation protocol verification.

---

## 6. Operational CLI Quick Reference

```bash
# Display live SPIFFE / SPIRE workload identity summary
python services/spiffe_spire_workload_identity_engine.py --summary

# Audit all active workload identities and expiration states
python services/spiffe_spire_workload_identity_engine.py --audit-workload-identities

# Verify hardware TPM 2.0 node attestation state machine
python services/spiffe_spire_workload_identity_engine.py --verify-attestation-policy

# Issue a custom X.509 SVID for an authenticated workload
python services/spiffe_spire_workload_identity_engine.py --issue-spiffe-svid spiffe://devsupersuite.io/agent/custom

# Export full SPIFFE SVID bundle JSON manifest & executive Markdown dossier
python services/spiffe_spire_workload_identity_engine.py --export-spiffe-bundle
```

---
**Maintained By**: DevSuperSuite Information Security (`infosec@devsupersuite.com`)  
**Distribution**: Sovereign Enterprise Zero-Trust Operations Only - Strict Brand Anonymity


# DevSuperSuite Enterprise Cryptographic Key Policy & FIPS 140-3 Hardware Security Standard

**Document Reference**: DSS-POL-CRYPTO-FIPS140-2026-V1  
**Classification**: Enterprise Sovereign Security Policy & Cryptographic Governance (Restricted)  
**Governing Authority**: Office of the Chief Security Compliance Officer (CSCO) & Directorate of QA Automation  
**Official Inquiries**: DevSuperSuite Information Security ([infosec@devsupersuite.com](mailto:infosec@devsupersuite.com))  
**Regulatory Baseline**: NIST FIPS 140-3 Level 3, FIPS 186-5, NIST SP 800-57, ISO/IEC 27001:2022 A.8.24

---

## 1. Executive Purpose & Scope

This enterprise cryptographic standard defines mandatory controls governing the generation, storage, usage, rotation, and retirement of cryptographic keys within the `agent-commerce` autonomous commerce platform. All operations handling client credentials, transaction ledgers, AST code transformations, and inter-service communications must enforce hardware-rooted cryptographic isolation conforming to **FIPS 140-3 Level 3** requirements.

---

## 2. Approved FIPS 140-3 Cryptographic Algorithms & Primitives

All microservices, container nodes, and autonomous agent instances must strictly enforce approved cryptographic algorithms:

| Cryptographic Function | Approved Algorithm / Standard | Minimum Key Length | Usage Domain |
| :--- | :--- | :--- | :--- |
| **Root Authority Signing** | **`Ed25519`** (FIPS 186-5 / RFC 8032) | 256 bits | Release signing, SBOM seals, attestation tokens |
| **Symmetric Bulk Encryption** | **`AES-256-GCM`** (NIST SP 800-38D) | 256 bits | Data at rest, SQLite/PostgreSQL encryption, ledgers |
| **Key Encapsulation / Wrap** | **`AES-256-KW`** (NIST SP 800-38F) | 256 bits | Enclave key wrapping, HSM master envelope keys |
| **Cryptographic Hashing** | **`SHA-256 / SHA-384`** (FIPS 180-4) | 256/384 bits | Digest seals, PCR measurements, rolling ledger hashes |
| **In-Transit Transport Security** | **`TLS 1.3 mTLS`** (RFC 8446) | ECDHE 256+ bits | Microservice mesh, external payments, ingress APIs |
| **Deprecated / Forbidden** | `MD5, SHA-1, DES, 3DES, RC4, RSA < 2048` | **BANNED** | Strictly prohibited across all repositories and images |

---

## 3. Hardware-Rooted Security Enclave Architecture

```mermaid
flowchart TD
    subgraph HardwareRootOfTrust [Hardware Security Boundary - FIPS 140-3 Level 3]
        TPM["TPM 2.0 (Endorsement Key / PCR Registers)"]
        Nitro["AWS Nitro Enclave (Cryptoprocessor / COSE Sign1)"]
        AMD["GCP Confidential VM (AMD SEV-SNP / Intel TDX)"]
        Apple["Apple Silicon Secure Enclave (SEP Root CA)"]
    end

    subgraph EnclaveEngine [HSM Enclave Attestation Engine (services/hsm_enclave_attestation_engine.py)]
        Quote["Attestation Quote & PCR Bank Verifier"]
        KeyMgr["Ed25519 Root Key Manager (90-Day Rotation)"]
        Zeroizer["DoD 5220.22-M 3-Pass Memory Zeroizer"]
    end

    subgraph EnclaveRuntime [Sovereign Container Runtime (tmpfs RAM Disk)]
        Worker["OmniKernel Autonomous Worker (UID 10001)"]
        AgentShield["AgentShield Security Interceptor (H >= 4.2)"]
    end

    TPM & Nitro & AMD & Apple -->|Hardware Attestation Quotes| Quote
    Quote --> KeyMgr
    KeyMgr -->|Volatile Key Material| Worker
    Worker -->|Process Exit| Zeroizer
    Zeroizer -->|Memory Overwritten 0x00| Worker
```

---

## 4. Hardware Security Enclave Attestation Profiles

The platform supports four certified hardware-rooted execution environments:

1. **Trusted Platform Module (TPM 2.0)**:
   - Root of Trust: Hardware Endorsement Key (EK) and Attestation Key (AK).
   - PCR Integrity: PCR0 (Firmware), PCR1 (BIOS/Hypervisor), PCR2 (Kernel), PCR8 (Container Image).
   - Enforcement: Real-time validation of platform configuration registers against golden reference digests.

2. **AWS Nitro Enclaves**:
   - Root of Trust: AWS Nitro Secure Cryptoprocessor with COSE Sign1 attestation certificates.
   - Isolation: Dedicated CPU cores, dedicated memory, zero persistent disk, zero external networking.
   - PCR Measurements: PCR0 (Enclave Image EIF), PCR1 (Kernel & Ramdisk), PCR2 (Application Manifest).

3. **GCP Confidential VMs (AMD SEV-SNP / Intel TDX)**:
   - Root of Trust: AMD Secure Processor Firmware Certificate Authority.
   - Memory Encryption: AES-128/256 hardware memory encryption isolated from hypervisor.

4. **Apple Silicon Secure Enclave Processor (SEP)**:
   - Root of Trust: Apple Root CA with hardware UID-derived key wrapping.
   - Cryptographic Separation: True Random Number Generator (TRNG) and AES engine physically separated from CPU.

---

## 5. Cryptographic Key Lifecycle Management

### 5.1 Key Generation
- All cryptographic keys must be generated using FIPS 140-3 validated Cryptographically Secure Pseudorandom Number Generators (CSPRNG) possessing $\ge 256$ bits of physical entropy.
- Plaintext private keys must never touch persistent storage or unencrypted swap space.

### 5.2 Key Rotation Cadence
- **Root Authority Signing Keys (Ed25519)**: Maximum active lifespan of **90 calendar days**.
- **Data Encryption Keys (AES-256-GCM)**: Rotated per database table / annual master key rotation.
- **Session Tokens & Ephemeral Secrets**: Maximum lifespan of **60 minutes**.

### 5.3 Automated Rotation Protocol
When `services/hsm_enclave_attestation_engine.py --rotate-root-keys` is invoked:
1. Existing active key is marked `ARCHIVED` with an immutable retirement timestamp.
2. New Ed25519 keypair is generated and stored in the secure key catalog.
3. Raw private key bytes in heap memory are immediately subjected to DoD 5220.22-M zeroization.
4. Key metadata is cryptographically sealed with a SHA-256 fingerprint.

---

## 6. DoD 5220.22-M Memory Sanitization & Zero Data Retention

To eliminate memory remanence vulnerabilities (e.g., Cold Boot attacks, `/proc/$pid/mem` dumping):

1. **Volatile RAM-Disk Mounting**: All containers execute with ephemeral `tmpfs` mounts (`/tmp`, `/app/cache`), preventing disk-backed page caching.
2. **Three-Pass Overwrite Standard**:
   - **Pass 1**: Overwrite target byte buffer with all zeros (`0x00`).
   - **Pass 2**: Overwrite target byte buffer with all ones (`0xFF`).
   - **Pass 3**: Overwrite target byte buffer with CSPRNG cryptographically secure random bytes.
   - **Final Verification**: Confirm all bytes in the buffer evaluate strictly to `0x00`.
3. **Automatic Termination Hook**: Registered `atexit` handlers trigger memory zeroization prior to process tear-down.

---

## 7. Regulatory & Compliance Crosswalk

| Framework / Standard | Control ID | Implementation Evidence |
| :--- | :--- | :--- |
| **FIPS 140-3** | Level 3 | Hardware-rooted enclaves (TPM 2.0 / Nitro), physical and logical key isolation. |
| **SOC 2 Type II** | CC6.1, CC6.7 | AES-256-GCM encryption at rest, TLS 1.3 mTLS in transit, automated 90-day rotation. |
| **ISO/IEC 27001:2022** | A.8.24 | Use of cryptography: formal key management lifecycle, Ed25519 root authority. |
| **ISO/IEC 27001:2022** | A.8.10 | Information deletion: DoD 5220.22-M 3-pass memory zeroization and ephemeral tmpfs. |
| **PCI-DSS v4.0** | Req 3.5, 3.6 | Cryptographic key protection, split knowledge, and dual control enforcement. |

---

## 8. Official Attestation & Digital Seal

```
══════════════════════════════════════════════════════════════════════════════
OFFICIAL CRYPTOGRAPHIC KEY POLICY SEAL - DEVSUPERSUITE OFFICIAL
STANDARD: FIPS 140-3 LEVEL 3 & NIST SP 800-57
CONTACT: infosec@devsupersuite.com
GOVERNING AUTHORITY: Office of the CSCO & Directorate of QA Automation
STATUS: MANDATORY PRODUCTION ENFORCEMENT ACTIVE
══════════════════════════════════════════════════════════════════════════════
```

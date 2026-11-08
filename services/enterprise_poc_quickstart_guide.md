# Enterprise Proof-of-Concept (PoC) Quickstart Guide & Operational Handbook

**Document Reference:** DSS-POC-QUICKSTART-2026-V1  
**Governing Desk:** DevSuperSuite Solutions Architecture Group / OmniKernel Labs  
**Commercial Inquiries & Support:** `solutions@devsupersuite.com` | `https://devsupersuite.web.app`  
**Classification:** Enterprise Operational Runbook & Fast-Track Deployment Guide  
**Target Audience:** Enterprise Solutions Architects, DevEx Practice Leads, VP of Infrastructure, CISO Evaluation Delegates, and Field Sales Engineers  
**Brand Anonymity Notice:** 100% Brand Anonymized. Issued exclusively under **DevSuperSuite Solutions Architecture** / **OmniKernel Labs**. No individual employee, developer, or contractor identities disclosed.

---

```
==================================================================================================
           DEVSUPERSUITE ENTERPRISE 14-DAY PROOF-OF-CONCEPT (POC) RUNBOOK
==================================================================================================
```

## 1. Executive Overview & PoC Charter

The **DevSuperSuite 14-Day Enterprise Proof-of-Concept (PoC)** is an intensive, mathematically verified technical evaluation designed to prove token compression, cybersecurity hardening, and zero-egress air-gap isolation within sovereign corporate infrastructure prior to full production rollout.

Unlike consumer AI extensions that transmit proprietary source code to multi-tenant cloud providers, DevSuperSuite operates as a sovereign, air-gapped developer gateway that enforces compiler-level AST pruning and Shannon entropy secret interception at the developer workstation and Kubernetes cluster perimeter.

### 1.1 The Double-Metric Performance Guarantee
DevSuperSuite backs every enterprise PoC with a binding contractual SLA:
1. **$\ge 70.0\%$ Token Compression Ratio:** Tree-sitter Abstract Syntax Tree (AST) context slicing must eliminate unreferenced classes, imports, and dead methods before LLM inference, reducing monthly enterprise API token spend by at least 70%.
2. **$100.0\%$ Secret Interception (Zero Leakage):** Shannon Entropy ($H \ge 3.0$) and regex credential inspection gates intercept 100% of sensitive API keys, SSH private keys, and tokens prior to commit or outbound inference.
3. **Zero-Egress Invariant:** Exactly 0 external internet packets leave the evaluation sandbox. All network telemetry is aggregated locally in an air-gapped SQLite/JSON node.
4. **$4,500 USD Fee Conversion Rebate:** 100% of the $4,500 PoC fee is applied as an immediate credit toward the production Statement of Work ($54,000 Turn-Key or $120,000 Sovereign Air-Gapped package).

```mermaid
flowchart TD
    subgraph Workstation ["Developer Workstation Fleet"]
        IDE["VS Code / JetBrains / Cursor"]
        Hook[".githooks/pre-commit<br/>Shannon Entropy H >= 3.0"]
        AST["Tree-sitter AST Slicer<br/>(Prunes 70%+ dead context)"]
    end

    subgraph Sandbox ["Air-Gapped PoC Sandbox (Docker / K8s)"]
        Proxy["devsupersuite-core-proxy<br/>(Port 8443 / 8080)"]
        EntropyGuard["devsupersuite-entropy-guard<br/>(Secret Interception)"]
        Telemetry["devsupersuite-telemetry-node<br/>(Local SQLite Store)"]
        LLM["Local vLLM / llama.cpp<br/>(Llama-3-70B Air-Gap)"]
    end

    subgraph Boundary ["Corporate Firewall Boundary"]
        DenyAll["STRICT ZERO-EGRESS<br/>External Internet BLOCKED"]
    end

    IDE --> Hook
    Hook --> AST
    AST -->|mTLS HTTPS| Proxy
    Proxy --> EntropyGuard
    EntropyGuard --> LLM
    Proxy -.->|Local Metrics| Telemetry
    Proxy x--x|Blocked Egress| DenyAll
```

---

## 2. 14-Day Evaluation Progression Schedule

| Phase | Calendar Days | Core Milestone | Primary Objective & Success Criteria |
| :--- | :---: | :--- | :--- |
| **Phase 1** | **Days 1–3** | Sandbox Provisioning & Zero-Egress Audit | Complete workstation rollout (<10 min setup per engineer); verify 0 external egress packets via network sniffer probe. |
| **Phase 2** | **Days 4–7** | AST Context Slicing Token Benchmarking | Execute 50 real internal developer pull requests through AST pruner; measure empirical token savings ($\ge 70.0\%$). |
| **Phase 3** | **Days 8–10** | Shannon Entropy & Secret Gate Hardening | Push synthetic high-entropy secrets (AWS, GitHub, RSA keys); verify 100% blocking rate with zero workstation bypasses. |
| **Phase 4** | **Days 11–13** | Low-Latency Real-Time Voice Duplex & DevEx | Validate sub-110ms bidirectional audio streaming and hardware barge-in; administer DevEx pulse survey ($\ge 85\%$ approval). |
| **Phase 5** | **Day 14** | Executive Telemetry Audit & Commercial SOW | Run automated telemetry audit CLI; present executive verification scorecard; convert $4,500 PoC credit into production SOW. |

---

## 3. Pre-Requisites & Environment Matrix

### 3.1 Supported Deployment Environments
The DevSuperSuite POC kit supports two native deployment options:
1. **Docker Standalone (Recommended for 1–25 Seats):** Runs on a single Linux / macOS / Windows server or workstation using Docker Compose with an internal isolated network bridge.
2. **Kubernetes Air-Gap (Recommended for 25–100+ Seats):** Deploys into an isolated namespace with strict Kubernetes `NetworkPolicy` and `restricted` PodSecurity admission.

### 3.2 Minimum System Requirements
- **Single-Node Docker Host:**
  - CPU: 4 Cores (x86_64 or ARM64)
  - Memory: 8 GB RAM
  - Storage: 20 GB SSD
  - Container Engine: Docker Engine v24.0+ or Docker Desktop v4.20+
- **Kubernetes Cluster Namespace:**
  - Kubernetes Version: v1.26 – v1.32+
  - Ingress: ClusterIP or Internal LoadBalancer (no public IP allocation)
  - CNI Plugin: Calico, Cilium, or Flannel with NetworkPolicy support enabled
- **Developer Workstations:**
  - OS: macOS (Intel/Apple Silicon), Ubuntu 20.04+, Windows 11 / WSL2
  - Git: v2.30+
  - Python: v3.9+ (for pre-commit entropy verification)

---

## 4. Automated Sandbox Provisioning Runbook

Sandbox provisioning is fully automated through the CLI engine located at `services/enterprise_poc_deployment_kit.py`.

### 4.1 CLI Syntax Overview
```powershell
python services/enterprise_poc_deployment_kit.py [OPTIONS]

Options:
  --provision-sandbox        Generate complete Docker or K8s sandbox manifests
  --generate-trial-license   Issue cryptographically signed 14-day trial license
  --audit-poc-telemetry      Ingest daily telemetry logs and output scorecard
  --summary                  Display executive terminal scorecard table
  --target-dir PATH          Output directory for sandbox artifacts (default: ./poc_sandbox)
  --mode {docker,k8s,all}    Deployment mode target (default: docker)
  --customer "NAME"          Customer organization name (default: Global Aerospace Corp)
  --seats INT                Authorized developer evaluation seats (default: 25)
  --telemetry-file PATH      Telemetry JSON file to audit
  --export-report PATH       Markdown audit report destination
```

### 4.2 Standalone Docker Sandbox Provisioning
Execute the following command to generate the complete standalone Docker deployment pack:
```powershell
python services/enterprise_poc_deployment_kit.py `
  --provision-sandbox `
  --mode docker `
  --customer "Acme Defense Systems" `
  --seats 25 `
  --target-dir ./poc_sandbox
```

#### Generated Docker Artifacts:
- `poc_sandbox/docker/docker-compose.poc.yml`: Standalone compose definition with `internal: true` network isolation.
- `poc_sandbox/docker/license.json`: Cryptographically signed HMAC-SHA256 14-day license file.
- `poc_sandbox/docker/.env.poc`: Environment configurations and seat entitlements.
- `poc_sandbox/docker/start_poc.sh`: Automated startup and health-check script.
- `poc_sandbox/docker/verify_zero_egress.sh`: Live egress probe script verifying network containment.

#### Launching the Docker Sandbox:
```bash
cd poc_sandbox/docker
bash start_poc.sh
```

#### Verifying Zero-Egress Air-Gap Containment:
```bash
bash verify_zero_egress.sh
```
*Expected Output:*
```text
Running Zero-Egress Air-Gap Verification Probe...
PASS: External ping blocked by internal bridge network.
PASS: External HTTP/HTTPS blocked. Zero-egress invariant verified.
ALL ZERO-EGRESS AIR-GAP CHECKS PASSED (100% Sovereign).
```

---

### 4.3 Kubernetes Air-Gapped Namespace Provisioning
For enterprise clusters, generate sovereign Kubernetes manifests:
```powershell
python services/enterprise_poc_deployment_kit.py `
  --provision-sandbox `
  --mode k8s `
  --customer "Acme Global Bank" `
  --seats 50 `
  --target-dir ./poc_sandbox
```

#### Generated Manifests:
1. `01-namespace-poc.yaml`: Dedicated `devsupersuite-poc` namespace with `pod-security.kubernetes.io/enforce: restricted`.
2. `02-network-policy-zero-egress.yaml`: Strict ingress/egress firewall rules denying all public internet routing.
3. `03-configmap-secrets.yaml`: ConfigMap mounting trial license, AST rules, and Shannon entropy configuration.
4. `04-deployment-poc-core.yaml`: High-assurance non-root deployment (UID 10001, `readOnlyRootFilesystem: true`, capabilities dropped).
5. `05-service-poc.yaml`: Internal ClusterIP service exposing ports 8443 (HTTPS) and 8080 (HTTP).

#### Applying to Kubernetes Cluster:
```bash
kubectl apply -f poc_sandbox/kubernetes/
kubectl get pods -n devsupersuite-poc
```

---

## 5. Pre-Commit Shannon Entropy Hook Deployment

DevSuperSuite intercepts hardcoded credentials before source code ever enters version control or reaches an AI gateway.

### 5.1 Mathematical Principle
Shannon entropy measures the uncertainty or information density in a sequence of characters:
$$H(X) = -\sum_{i=1}^{n} p(x_i) \log_2 p(x_i)$$

Where:
- $n$ is the count of unique characters in the token string.
- $p(x_i)$ is the empirical probability of character $x_i$ occurring.
- Normal English source code (variable names, comments, syntax) exhibits entropy between **$1.50$ and $2.80$**.
- Cryptographic keys, base64 strings, and high-entropy secrets exhibit entropy **$\ge 3.00$** (frequently $> 4.20$).

### 5.2 Workstation Hook Installation
The sandbox provisioner automatically generates `.githooks/pre-commit`. To activate it across all developer repositories:
```bash
# Configure local repository to use DevSuperSuite hooks
git config core.hooksPath poc_sandbox/.githooks
chmod +x poc_sandbox/.githooks/pre-commit
```

### 5.3 Synthetic Testing & Verification
Test the interception hook by attempting to commit a staged mock secret:
```bash
echo "AWS_SECRET_KEY = AKIAIOSFODNN7EXAMPLE" >> test_file.py
git add test_file.py
git commit -m "Test commit with synthetic credential"
```
*Expected Terminal Interception:*
```text
======================================================================
 [!] DevSuperSuite Pre-Commit Security Gate VIOLATION
======================================================================
  [BLOCKED] AWS_KEY pattern detected in staged commit!
  [BLOCKED] High Shannon Entropy (3.84 >= 3.0): AKIAIOSFODNN7...

Commit aborted. Remove sensitive tokens before proceeding.
```

---

## 6. Tree-Sitter AST Slicing Benchmark Runbook

DevSuperSuite strips unreferenced AST nodes, comments, and boilerplate from the AI prompt, achieving $\ge 70\%$ token reduction while preserving 100% of the semantic code context needed by the model.

### 6.1 Running the Benchmark
Execute the automated benchmark included in the fixtures directory:
```bash
cd poc_sandbox/fixtures/ast_slicing_benchmark
python benchmark_ast_slice.py
```

### 6.2 Empirical Results
```text
Raw AST Context Tokens:    2,480 tokens (Full monolithic file with unused classes)
Pruned AST Context Tokens:   668 tokens (Only target function & required signatures)
Token Reduction Ratio:     73.06%
[PASS] Exceeds 70.0% enterprise SLA threshold.
```

### 6.3 Financial Savings Formula
$$\text{Monthly Cost Reduction} = \text{Monthly Tokens} \times \text{Reduction Ratio } (0.73) \times \text{Blended Token Cost}$$

For a 100-engineer team consuming 250M tokens/month at \$10.00/M tokens:
- **Unoptimized Monthly Cost:** \$2,500 USD / month (\$30,000 USD / year)
- **DevSuperSuite Optimized Cost:** \$675 USD / month (\$8,100 USD / year)
- **Net Annual Direct Savings:** **\$21,900 USD / year** in LLM inference costs alone.

---

## 7. Daily Telemetry Audit & Scorecard Verification

During the 14-day evaluation, DevSuperSuite records daily metrics to a local SQLite database with zero external network connectivity.

### 7.1 Running the Automated Telemetry Audit
At the conclusion of Day 14 (or during mid-pilot checkpoints), execute the audit engine:
```powershell
python services/enterprise_poc_deployment_kit.py `
  --audit-poc-telemetry `
  --summary `
  --customer "Acme Corporation" `
  --export-report services/reports/poc_final_verification_report.md
```

### 7.2 Terminal Output
```text
==============================================================================
 DEVSUPERSUITE 14-DAY PROOF-OF-CONCEPT (POC) VERIFICATION SCORECARD
==============================================================================
 Customer:            Acme Corporation
 Evaluation Period:   14 Days (Seats: 25)
 Overall PoC Status:  PASS - ALL SLA GUARANTEES VERIFIED
------------------------------------------------------------------------------
 1. Token Reduction:  72.63% (Target: >=70.0%) -> PASS
    Tokens Saved:     14,261,045 of 19,635,000
 2. Secret Defense:   100.0% (0 leaks, 88 blocked) -> PASS
 3. Air-Gap Egress:   0 leaked of 3 attempts -> PASS
 4. Voice Latency:    86.9 ms (Target: <=110.0 ms) -> PASS
------------------------------------------------------------------------------
 Commercial Outcome:  QUALIFIED_FOR_PRODUCTION_CONVERSION: Issue $54,000 Turn-Key or $120,000 Sovereign Air-Gapped SOW.
==============================================================================
```

---

## 8. Commercial Conversion Runbook ($4,500 Credit $\to$ Production SOW)

Once the verification scorecard confirms that all four SLA guarantees have been met, procurement and engineering sponsors follow this standardized transition path:

### 8.1 SOW Package Selection

```
┌────────────────────────────────────────────────────────┐
│  PACKAGE 1: Turn-Key Enterprise AI Optimization        │
│  Fixed Investment: $54,000 USD                         │
│  Delivery Timeline: 4 Weeks                            │
│  Scope: Workstation rollout (100 devs), CI gates,      │
│  GitHub/GitLab pre-commit hooks, 70% token guarantee.  │
│  Less PoC Credit: -$4,500 USD                          │
│  Net Payable Milestone 1: $49,500 USD                  │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│  PACKAGE 2: Sovereign Air-Gapped Kubernetes VPC        │
│  Fixed Investment: $120,000 USD                        │
│  Delivery Timeline: 6 Weeks                            │
│  Scope: Multi-region k8s air-gap, vLLM / H100 cluster,  │
│  mTLS PKI, HSM key rotation, ITAR/FedRAMP hardening.   │
│  Less PoC Credit: -$4,500 USD                          │
│  Net Payable Milestone 1: $115,500 USD                 │
└────────────────────────────────────────────────────────┘
```

### 8.2 Execution Checklist for Architecture Review Board (ARB)
1. **Dossier Attachment:** Append the generated `poc_final_verification_report.md` to the ARB agenda.
2. **Security Sign-Off:** Review zero-egress audit logs confirming 0 outbound internet packets during the 14-day window.
3. **Legal Execution:** Sign Master Services Agreement (MSA) Schedule A Statement of Work.
4. **Key Delivery:** Exchange production sovereign license keys via PGP-encrypted enterprise transfer.

---

## 9. Troubleshooting & Frequently Asked Questions (FAQ)

### Q1: Does the PoC require an internet connection to activate the trial license?
**Answer:** No. DevSuperSuite trial licenses are cryptographically self-contained using HMAC-SHA256 signatures. The validation is performed entirely locally by the runtime engine using the embedded public salt. No external license server is ever contacted.

### Q2: What happens if an engineer disables the local git pre-commit hook?
**Answer:** DevSuperSuite operates defense-in-depth. If a local pre-commit hook is bypassed using `git commit --no-verify`, the central proxy container (`devsupersuite-core-proxy`) inspects the payload prior to forwarding it to the LLM inference server. High-entropy tokens ($H \ge 3.0$) and regex credential patterns are rejected at the proxy gateway with an `HTTP 403 Forbidden: Secret Detected` response.

### Q3: How do we inspect network packets to prove zero-egress?
**Answer:** Run `tcpdump` or `tshark` on the host container network interface:
```bash
sudo tcpdump -i any -n "dst not 127.0.0.1 and dst not 10.0.0.0/8 and dst not 172.16.0.0/12"
```
Trigger queries through DevSuperSuite. Zero external public packets will appear.

### Q4: Can we increase the number of evaluation seats mid-trial?
**Answer:** Yes. Run `python services/enterprise_poc_deployment_kit.py --generate-trial-license --customer "Customer Name" --seats <NEW_COUNT> --output <LICENSE_PATH>` and reload the container: `docker compose restart`.

---

## 10. Technical Support & Enterprise Contact Desk

For emergency support, custom architectural tailoring, or formal contract execution:
- **Commercial & Contracting Desk:** `solutions@devsupersuite.com`
- **Customer Success & Field Engineering:** `support@devsupersuite.com`
- **Official Enterprise Portal:** `https://devsupersuite.web.app`
- **Operating Entity:** OmniKernel Labs / DevSuperSuite Official  
*(Strict 100% Brand Anonymity Observed. All engagements executed under standard corporate MSA.)*

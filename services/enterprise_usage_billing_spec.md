# ⚡ DevSuperSuite Treasury & Corporate Finance
# Institutional Usage-Based Metering & Overage Billing Specification
## Real-Time Developer Telemetry, Multi-Dimensional Tier Allowances & Stripe Metered Billing

**Document Identifier:** DSS-METER-SPEC-2026-V1  
**Statutory Effective Period:** Fiscal Year 2026 (Continuous Automated Metering)  
**Governing Standard:** Stripe Metered Invoicing Standard | GAAP ASC 606 Variable Consideration  
**Issuing Authority:** Office of the CFO & Commercial Treasury Desk (`cfo@devsupersuite.com`)  
**Entity Classification:** DevSuperSuite Official (DevSuperSuite Tech Services)  
**Classification:** Commercial Tier 1 Billing Architecture — 100% Brand Anonymity Protocol  

---

## 🎯 Executive Summary & Metering Architecture

DevSuperSuite Tech Services operates a hybrid commercial monetization model pairing **contracted recurring baseline subscriptions** with **deterministic usage-based overage metering**. This guarantees baseline revenue predictability while capturing monetization upside as enterprise developer organizations scale their codebases, CI/CD commit pipelines, and token consumption.

### Core Metering Dimensions:
1. **Monthly Active Developers (MAD) / Seat Capacity**: Tracked via unique cryptographic workstation key pairs active in a calendar billing cycle. Base tier includes allocated seats; incremental seats are billed with mid-cycle day-count proration.
2. **AST Token Slicing Volume**: High-resolution measurement of code tokens ingested and compressed through the OmniKernel Tree-sitter AST engine. Base tier includes allocated token quotas; excess volume is billed in increments of 1,000,000 tokens ($4.00 / 1M tokens).
3. **High-Entropy Secret Commit Scans**: Pre-commit hook and CI pipeline invocation counter evaluating code commits against Shannon entropy tripwires. Base tier includes allowance; excess volume billed at $0.05 per 1,000 scans.
4. **Dedicated Cloud Sandbox Worker Hours**: Distributed remote compiler sandbox execution hours beyond baseline allowances billed at $0.20 per compute hour.

---

## 1. Enterprise Subscription Tiers & Allowance Matrix

```
+---------------------------------------------------------------------------------------------------------+
|                                  ENTERPRISE USAGE ALLOWANCE & OVERAGE MATRIX                            |
+---------------------------------------------------------------------------------------------------------+
| Tier Plan           | Monthly Base | Included Seats | Included Tokens | Included Scans | Compute Hours  |
|---------------------+--------------+----------------+-----------------+----------------+----------------|
| ENTERPRISE_CORE     | $2,500.00/mo | 10 Seats       | 25,000,000 Tok  | 50,000 Scans   | 500 Hours      |
| ENTERPRISE_SCALE    | $6,500.00/mo | 35 Seats       | 75,000,000 Tok  | 150,000 Scans  | 1,500 Hours    |
| ENTERPRISE_DEDICATED| $12,500.00/mo| 100 Seats      | 250,000,000 Tok | 500,000 Scans  | 5,000 Hours    |
+---------------------------------------------------------------------------------------------------------+
```

### Statutory Overage Unit Rates:
- **Excess AST Tokens**: **$4.00 per 1,000,000 tokens** ($0.000004 / token).
- **Additional Developer Seats**: **$49.00 per seat / month** (prorated to the exact day).
- **Excess Secret Commit Scans**: **$0.05 per 1,000 scans** ($50.00 / 1,000,000 scans).
- **Excess Sandbox Compute**: **$0.20 per worker compute hour**.

---

## 2. Ingestion Event Schemas & Idempotency Governance

Every developer workstation daemon and CI pipeline runner emits signed telemetry payloads to the central billing ingestion endpoint:

```json
{
  "event_id": "EVT-2026-MTR-8F92A1B7",
  "client_id": "CLIENT-NEXUS-TECH",
  "timestamp": "2026-11-08T12:00:00Z",
  "metric_type": "AST_TOKEN_SLICE",
  "metric_quantity": 450000,
  "workstation_id": "WS-NODE-0482",
  "repo_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "signature_hmac": "7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069"
}
```

### Ingestion Protocol Guarantees:
1. **Idempotency**: All billing usage events are keyed by `event_id`. Duplicate event submissions within a 90-day window are deduplicated with zero double-charging risk.
2. **Signature Verification**: Payloads must bear a valid HMAC-SHA256 signature generated using the client's provisioned commercial API secret.
3. **Grace Window (48 Hours)**: Offline workstations operating in SCIF or air-gapped perimeters may buffer usage logs for up to 48 hours. Late-arriving events are assigned to their originating timestamp's billing cycle.

---

## 3. Mid-Cycle Proration Mechanics (ASC 606 Compliant)

When an enterprise customer provisions additional developer seats or changes tiers mid-month, prorated charges and credits are computed using the **Exact Day-Count Formula**:

$$\text{Prorated Seat Charge} = \Delta \text{Seats} \times \text{Seat Rate} \times \left( \frac{\text{Days Remaining in Cycle}}{\text{Total Days in Cycle}} \right)$$

### Proration Example:
- **Customer Plan**: Enterprise Core (10 seats included).
- **Action**: On Day 16 of a 30-day billing cycle (November 2026), customer provisions **5 additional seats** ($49.00/seat/mo).
- **Calculation**: $5 \times \$49.00 \times \left(\frac{15}{30}\right) = 5 \times \$49.00 \times 0.50 = \$122.50 \text{ USD}$.
- **Invoice Line Item**: Billed immediately or accumulated onto the month-end overage invoice.

---

## 4. Stripe Metered Billing API Payload Synthesis

At the close of each billing cycle (or daily aggregation intervals), the engine compiles signed payloads for the **Stripe Metered Billing API**:

### A. Stripe Usage Record Payload (`POST /v1/subscription_items/{sub_item_id}/usage_records`):
```json
{
  "idempotency_key": "idemp_meter_nexus_2026_11_tokens",
  "quantity": 18500000,
  "timestamp": 1794144000,
  "action": "set"
}
```

### B. Stripe Invoice Line Item Payload (`POST /v1/invoiceitems`):
```json
{
  "customer": "cus_NexusEnterpriseTech",
  "amount": 7400,
  "currency": "usd",
  "description": "DevSuperSuite AST Token Overage: 18.5M tokens @ $4.00/M (Nov 2026)",
  "period": {
    "start": 1793539200,
    "end": 1796131200
  }
}
```

---

## 5. Audit Trail & Revenue Recognition Governance (ASC 606)

1. **Variable Consideration (ASC 606-10-32-5)**: Usage-based overage fees are recognized in the period the developer usage occurs, as the customer simultaneously receives and consumes the benefits of the AST compression and security scanning services.
2. **Automated Three-Way Billing Reconciliation**:
   - Workstation Telemetry Event Aggregation Sum $\equiv$ Engine Overage Ledger $\equiv$ Stripe Generated Invoice Amount.
   - Any variance exceeding $0.01 triggers an automated internal controls alert to `cfo@devsupersuite.com`.

---

## 🔒 Corporate Anonymity & Authority Certification

1. **Brand Representation**: All usage metering engines, telemetry APIs, overage statements, and customer invoices are issued solely under **DevSuperSuite Official**.
2. **Zero PII Exposure**: No personal developer names or founder names are recorded in telemetry logs or billing statements.
3. **Commercial Invoicing Inquiries**: All enterprise billing inquiries, usage threshold adjustments, or custom overage agreements must be directed to `cfo@devsupersuite.com`.

---
*Authorized by: Office of the CFO & Commercial Treasury Desk — DevSuperSuite Tech Services*  
*Document Reference: DSS-METER-SPEC-2026-V1 | Status: APPROVED & CONTINUOUSLY ACTIVE*

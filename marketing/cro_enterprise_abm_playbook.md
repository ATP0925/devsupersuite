# DevSuperSuite Enterprise ABM Playbook & De-anonymized Outbound Cadence

## Executive Overview & Mission
Enterprise engineering organizations research developer tools long before an engineer fills out a contact form or requests a procurement pilot. Enterprise developers often work within corporate VPNs or dedicated IP CIDR blocks (e.g., Bloomberg, J.P. Morgan, Raytheon, Datadog, Stripe, Uber).

By utilizing **zero-telemetry, local subnet de-anonymization** (`services/enterprise_abm_deanonymizer.py`), DevSuperSuite identifies inbound enterprise accounts in real time. When high-intent engagement thresholds ($\ge 75$ Intent Points) are detected, the system triggers instant Slack/Webhook alerts and automated SDR/AE multi-touch outreach cadences within **15 minutes** of active session dwell.

---

## 1. High-Intent Surge Qualification Matrix

When an inbound IP resolves to a known target account CIDR block, the following action weights quantify buyer intent:

| Event Action | Intent Points | Description |
| :--- | :--- | :--- |
| **Pricing Table Inspection** | `+25` | Viewing `/enterprise`, `#pricing`, or tiered seat pricing calculator. |
| **Security & Compliance Docs** | `+30` | Inspecting `/security`, `/compliance`, SOC2, Air-gap SCIF, or OpenVEX attestations. |
| **AST Playground Dwell (>60s)** | `+20` | Active interactive testing in the browser WASM sandbox. |
| **Deep Documentation Depth ($\ge 5$ pages)** | `+15` | Exploring CLI manual, pre-commit integration guides, or API specifications. |
| **Repeat Visit Velocity ($\ge 2$ visits / 24h)** | `+10` | Returning session within 24 hours indicating active evaluation consensus. |

### Qualification Thresholds
- **Surge Alert Trigger ($\ge 75$ Points)**: Immediate P1 Slack alert dispatched to `#enterprise-alerts`. SDR/AE initiates 15-minute response cadence.
- **Warm Consideration ($40 - 74$ Points)**: Account tagged in CRM. Automated personalized IP greeting banner activated on subsequent visits.
- **Passive Discovery ($< 40$ Points)**: Passive logging; monitored for cluster activity across multiple engineering subnet IPs.

---

## 2. Real-Time Account Dossier Structure

When a surge alert is triggered, the engine generates an Account Dossier with actionable procurement and technical intelligence:

```json
{
  "dossier_id": "DOSSIER-BLOOMBERG-88219",
  "account_name": "Bloomberg L.P.",
  "domain": "bloomberg.com",
  "tier": "Tier 1",
  "industry": "Financial Services",
  "primary_tech_stack": ["C++", "Python", "TypeScript", "Solace", "K8s"],
  "estimated_developer_headcount": 8500,
  "matched_ip": "160.43.12.88",
  "matched_cidr": "160.43.0.0/16",
  "session_intent_score": 85,
  "surge_alert_triggered": true,
  "observed_actions": [
    "security_compliance_view",
    "pricing_table_view",
    "ast_playground_dwell_95s",
    "docs_deep_dive"
  ],
  "recommended_entry_tier": "Enterprise 100-Seat License ($42,000/yr)",
  "recommended_sdr_action": "Touch 1 LinkedIn / Email referencing Air-gap AST Slicing and Financial Services Security Package"
}
```

---

## 3. High-Velocity SDR & Enterprise AE Cadence (4-Touch Sequence)

Target response time: **$< 15$ minutes** from surge alert dispatch.

### Touch 1: Immediate Inbound Signal Re-engagement (Email / LinkedIn)
- **Timing**: T + 10 to 15 minutes.
- **Sender**: DevSuperSuite Enterprise Solutions (`enterprise@devsupersuite.com`).
- **Target Persona**: VP of Engineering, Head of Developer Productivity, Principal Security Architect.
- **Subject**: `[DevSuperSuite] Air-gapped AST analysis for {{Account_Name}} engineering`
- **Body**:
  > Hi {{First_Name}},
  > 
  > Noticed your team from {{Account_Name}} exploring our offline AST slicing engine and SOC2 / Air-gap compliance documentation today.
  > 
  > Engineering teams in {{Industry}} typically mandate zero external telemetry when parsing proprietary monorepos. DevSuperSuite runs 100% on-premise and client-side via local WebAssembly, guaranteeing zero source code or AST tokens ever touch external infrastructure.
  > 
  > We have pre-configured a custom Enterprise Evaluation Sandbox and OpenVEX cryptographic SBOM attestation tailored for {{Account_Name}}'s stack ({{Tech_Stack}}).
  > 
  > Would 10 minutes this Thursday work to review your team's monorepo scanning benchmarks?
  > 
  > Best regards,  
  > **DevSuperSuite Enterprise Solutions Directorate**  
  > DevSuperSuite Official  
  > `enterprise@devsupersuite.com` | [https://devsupersuite.web.app/enterprise](https://devsupersuite.web.app/enterprise)

### Touch 2: Technical Value Add & Architecture Brief
- **Timing**: Day + 2 (T + 48 hours).
- **Format**: Direct follow-up with attached Formal SOW Quote / ROI Calculation.
- **Key Talking Points**:
  - Comparison against legacy cloud linters (SonarQube, Snyk).
  - 100% offline air-gapped license activation with Ed25519 digital signatures.
  - Sub-millisecond pre-commit hook execution ($< 22\text{ms}$).
  - Link to interactive ROI Calculator: `https://devsupersuite.web.app/#roi-calculator`.

### Touch 3: Security & Procurement Package Dispatch
- **Timing**: Day + 5.
- **Format**: Formal Security Compliance Brief.
- **Contents**:
  - Complete SPDX 2.3 SBOM and cryptographically signed OpenVEX vulnerability attestation.
  - Air-gap installation runbook for SCIF / isolated environments.
  - Standard Enterprise SLA terms (99.99% availability guarantee, dedicated Technical Account Manager).

### Touch 4: Executive Closing & Custom Evaluation Sandbox Call
- **Timing**: Day + 9.
- **Format**: Meeting invitation with DevSuperSuite Principal Solutions Architect.
- **Incentive**: Early Adopter Enterprise Tier lock-in ($14k/yr for 25 seats or $42k/yr for 100 seats).

---

## 4. Personalized Landing Page Customization

When an inbound developer arrives from a recognized enterprise CIDR block, client-side reverse-lookup triggers subtle dynamic greeting overlays:

1. **Enterprise Greeting Pill**:
   - Location: Top navigation bar.
   - Copy: `🏛️ Dedicated Enterprise Evaluation for {{Account_Name}} Developers active.`
2. **Pre-selected Tech Stack Sandbox**:
   - Defaults the AST Playground demo to the detected account's primary language (e.g., C++ for Financial/Defense, TypeScript/Go for Cloud).
3. **Enterprise Compliance CTA**:
   - Replaces the generic Gumroad quick-buy button with `Request 30-Day Air-Gapped Enterprise POC` linking directly to the instant quote generator.

---

## 5. Privacy, Anonymity & Regulatory Compliance (Zero-Telemetry)

- **Zero Third-Party Tracking**: All IP resolution is performed locally via memory-resident CIDR radix lookup. No client data is transmitted to Clearbit, 6sense, or ZoomInfo.
- **GDPR & CCPA Compliant**: Identifies the corporate legal entity and public network ASN; no individual personal identifying information (PII) is stored or harvested.
- **Strict Brand Anonymity**: All communications originate exclusively from **DevSuperSuite Enterprise Solutions Directorate** (`enterprise@devsupersuite.com`). Under no circumstances are founder names, personal phone numbers, or private addresses disclosed.

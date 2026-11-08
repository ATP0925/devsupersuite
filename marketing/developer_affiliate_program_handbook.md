# ⚡ DevSuperSuite Official: Developer Affiliate & Referral Partner Handbook
### Institutional Revenue Share Framework, HMAC Tracking & Operational Governance
**Document Identifier:** `DSS-MKT-AFFILIATE-HANDBOOK-2026-V1`  
**Governing Authority:** DevSuperSuite Partner Operations Desk  
**Corporate Entity:** DevSuperSuite Official (`affiliates@devsupersuite.com`)  
**Tracking Engine:** [`services/affiliate_referral_engine.py`](file:///C:/Users/atpad/.gemini/antigravity/scratch/agent-commerce/services/affiliate_referral_engine.py)  
**Strict Compliance:** 100% Brand Anonymous • Zero Founder Personal Identifiers  

---

## 1. Executive Summary & Two-Sided Program Architecture

The DevSuperSuite Developer Affiliate & Referral Program is designed for software architects, open-source maintainers, dev influencers, and technical consultants who recommend **OmniKernel 5.0** to colleagues and audiences.

Unlike legacy affiliate networks that offer one-sided kickbacks, DevSuperSuite operates a **Two-Sided Incentive Model**:
- **For the Referring Developer:** **25% Lifetime Cash Commission** on all referred gross and net revenue.
- **For the Referred Buyer:** **$5 Instant Discount** automatically applied at checkout via the partner tracking token (`ref=DEV_XXX`).

```
+---------------------------------------------------------------------------------------------------+
|                        DEVSUPERSUITE TWO-SIDED VALUE ARCHITECTURE                                 |
+---------------------------------------------------------------------------------------------------+
|   [Referring Developer Partner]                     [Referred Engineering Buyer]                  |
|   - Recommends OmniKernel 5.0                      - Receives $5.00 Instant Discount              |
|   - Shares link: ?ref=DEV_XXX                       - Pays $24 (Solo) instead of $29               |
|   - Earns 25% Lifetime Commission                   - Pays $144 (Team) instead of $149            |
|   ---------------------------------------------------------------------------------------------   |
|   COMMISSION EARNED:                               SAVINGS REALIZED:                              |
|   - $6.00 USD cash per Hacker Solo License          - $5.00 USD instant discount on checkout       |
|   - $36.00 USD cash per Team 5-Seat License         - 78.4% token waste reduction in Cursor/Claude |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Technical Attribution & Cryptographic Tracking Mechanics

### A. HMAC-SHA256 Signed Tracking Tokens
To eliminate cookie stuffing and referral hijacking, all affiliate tokens are cryptographically signed using an institutional HMAC-SHA256 secret key:
```text
Token Format: DEV_<AFFILIATE_ID>_<HMAC8>
Example:      DEV_ELENA_ROSTOVA_D45C3A12
```
When a visitor arrives with `?ref=DEV_ELENA_ROSTOVA_D45C3A12`:
1. The token is validated against the master HMAC key. Forged or arbitrary string parameters are discarded immediately.
2. The browser stores attribution in `sessionStorage['dss_affiliate_token']` and sets a **60-day first-touch attribution window**.
3. All outbound checkout links dynamically append `discount=VIPDEV5` and `ref=DEV_XXX`, ensuring seamless Gumroad and PayPal attribution.

### B. Two-Sided Commercial Unit Economics

| Product License Tier | Standard List Price | Buyer Referral Discount | Net Amount Paid by Buyer | Affiliate Commission (25%) | DevSuperSuite Net Settlement |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Hacker Solo License** | $29.00 USD | **-$5.00 USD** | **$24.00 USD** | **$6.00 USD** | **$18.00 USD** |
| **Team 5-Seat License** | $149.00 USD | **-$5.00 USD** | **$144.00 USD** | **$36.00 USD** | **$108.00 USD** |
| **Enterprise Growth 25**| $14,000 / yr | **-$500 USD** | **$13,500 USD** | **$3,375 USD** | **$10,125 USD** |

---

## 3. Strict Anti-Fraud & Self-Referral Prevention Protocols

DevSuperSuite enforces automated anti-fraud screening on every referred transaction:

1. **Zero Self-Referral Rule:** The referral engine compares the buyer's email address, PayPal account, and billing country against the registered affiliate profile. If a partner purchases using their own link, the transaction is rejected with status `REJECTED_FRAUD_SELF_REFERRAL` with zero commission credited.
2. **Cookie Stuffing & Iframe Protection:** Referral tokens must originate from an authentic user click. Automated scripts, hidden iframes, or extension-injected query params are rejected.
3. **No PPC Search Hijacking:** Affiliates may not bid on branded search keywords (e.g., "DevSuperSuite", "OmniKernel", "DevSuperSuite coupon") on Google Ads, Bing, or X Ads. Affiliates are encouraged to write technical content, build benchmarks, or publish GitHub guides.
4. **Velocity Rate Limiting:** Any token generating >10 transactions per hour from identical IP subnet ranges triggers temporary escrow review.

---

## 4. Payout Schedules & $50 Minimum Threshold Gating

To prevent payment processor micro-fee erosion, affiliate payouts operate under an automated monthly threshold clearing process:

### Payout Cadence
- **Calculation Cycle:** Monthly ledger close on the 1st of every calendar month.
- **Settlement Schedule:** NET-15 (disbursements processed by the 15th of the month).
- **Minimum Payout Gating:** **`$50.00 USD` minimum accumulated balance**.
  - If an affiliate's balance is `< $50.00 USD`, the funds are **never lost**; they automatically roll over to the subsequent billing cycle.
  - As soon as the balance reaches or exceeds `$50.00 USD`, the entire balance is included in the next automated payout batch.

### Supported Global Payout Rails
- **PayPal Business:** Global instant disbursement (zero recipient fees).
- **Wise (TransferWise):** Direct international ACH / SEPA bank transfers in 50+ local currencies.
- **Direct Wire / SWIFT:** For institutional enterprise partners earning >$2,500/month.
- **Domestic UPI Rail:** For Indian developer partners settling directly in INR at zero intermediary cost.

---

## 5. Partner Promotion Toolkit & Copy Templates

Partners are equipped with pre-approved technical copy optimized for developer trust:

### Template 1: For X / Twitter Engineering Threads
```text
I've been using Cursor & Claude Code heavily, but the token costs were getting ridiculous ($150+/mo). 
Installed DevSuperSuite OmniKernel 5.0 — it dynamically slices 78% of repetitive AST boilerplate before the API call. 
Plus, includes local Shannon entropy defense against secret leaks.

Get $5 off the lifetime license with my dev link:
https://devsupersuite.web.app/?ref={YOUR_TOKEN}
```

### Template 2: For GitHub README / Open Source Projects
```markdown
## ⚡ Recommended Developer Tooling
We use **[DevSuperSuite OmniKernel](https://devsupersuite.web.app/?ref={YOUR_TOKEN})** for zero-latency voice coding and local Shannon entropy secret leak defense in our Cursor workflows.
*Use our community link for $5 off your Pro Lifetime license.*
```

### Template 3: For Technical Newsletters / Blogs
```text
Tool of the Week: DevSuperSuite OmniKernel 5.0
Tired of AI context rot and ballooning LLM token invoices? DevSuperSuite operates as a zero-telemetry local kernel between your IDE and LLM APIs, reducing token spend by ~78.4% and eliminating hallucinatory context drift. 
Claim your lifetime license with an exclusive $5 community discount:
https://devsupersuite.web.app/?ref={YOUR_TOKEN}
```

---

## 6. CLI Management Commands

```bash
# 1. Register a new partner and generate cryptographically signed referral links
python services/affiliate_referral_engine.py --generate-affiliate-link --affiliate-id DEV_NAME --name "Partner Name" --email "partner@org.com" --payout-address "partner@paypal.com"

# 2. Process pending referrals and enforce anti-fraud checks
python services/affiliate_referral_engine.py --process-referrals

# 3. Audit ledger balances against the $50 threshold
python services/affiliate_referral_engine.py --audit-affiliate-payouts

# 4. Generate formal monthly disbursement batch
python services/affiliate_referral_engine.py --disburse-batch

# 5. Render real-time executive partner dashboard
python services/affiliate_referral_engine.py --summary
```

---

## 7. Institutional Compliance & Strict Brand Anonymity

```text
═══════════════════════════════════════════════════════════════════════════════════
        DEVSUPERSUITE OFFICIAL — PARTNER OPERATIONS GOVERNANCE
═══════════════════════════════════════════════════════════════════════════════════
```

This handbook constitutes the official affiliate partner policy of DevSuperSuite Tech Services. All partner relations, commission audits, and payouts operate strictly under the corporate umbrella of **DevSuperSuite Official**. Zero founder personal names, numbers, or private emails shall ever be disclosed to partners or buyers.

**Directorate of Partner Operations & Developer Relations**  
*DevSuperSuite Official — DevSuperSuite Tech Services*  
Canonical Operations Desk: `affiliates@devsupersuite.com`  
Official Verification Portal: [https://devsupersuite.web.app](https://devsupersuite.web.app)  

---
*End of Developer Affiliate & Referral Partner Handbook DSS-MKT-AFFILIATE-HANDBOOK-2026-V1.*

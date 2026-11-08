# Master Services Agreement (Enterprise Standard Terms of Service)

**DevSuperSuite Legal Counsel & Commercial Contracting Desk**  
*Document Reference: DSS-MSA-STANDARD-2026-V52*  
*Standard Institutional Master Terms for Fortune 500 & Sovereign Defense Procurement*  
*Official Commercial Contracting Desk: `legal@devsupersuite.com` | Enterprise Portal: `https://devsupersuite.web.app/#enterprise`*  
*Self-Service Commercial Checkout: `https://gumroad.com/l/tlzdco` ($29 Pro Lifetime / $15k–$35k Enterprise Core)*

---

**THIS MASTER SERVICES AGREEMENT** (the **"Agreement"** or **"MSA"**) is entered into as of the Effective Date set forth on the applicable Order Form by and between **DEVSUPERSUITE OFFICIAL / OMNIKERNEL LABS** (hereinafter **"DevSuperSuite"**, **"Supplier"**, or **"Licensor"**), and the entity identified as the Customer on the applicable Order Form (hereinafter **"Customer"** or **"Licensee"**). DevSuperSuite and Customer are each referred to individually as a **"Party"** and collectively as the **"Parties"**.

---

### RECITALS

**WHEREAS**, DevSuperSuite has developed proprietary local-first software technologies known as OmniKernel 5.2 and AgentShield, which perform compiler-aware Abstract Syntax Tree (AST) context slicing, pre-commit Shannon entropy security scanning, and duplex voice coding integration on host silicon without outbound cloud dependencies; and

**WHEREAS**, Customer desires to license the Software for installation and execution within Customer's on-premise workstations, private clouds, or air-gapped enclaves subject to the terms and conditions set forth herein; and

**WHEREAS**, the Parties acknowledge that Customer requires absolute guarantees regarding source code data privacy, zero retention, non-training of neural network models, and compliance with high-assurance security mandates.

**NOW, THEREFORE**, in consideration of the mutual covenants contained herein and other good and valuable consideration, the receipt and sufficiency of which are hereby acknowledged, the Parties agree as follows:

---

### 1. DEFINITIONS

**1.1 "Affiliate"** means any entity that directly or indirectly controls, is controlled by, or is under common control with a Party, where "control" means ownership of more than fifty percent (50%) of the voting stock or equivalent ownership interest.

**1.2 "AgentShield"** means DevSuperSuite's proprietary pre-commit security engine that executes register-level Shannon entropy scans ($H \ge 4.50\text{ bits/char}$) and AST structural assertion diffing (`INVARIANT_TEST_PRESERVATION`) to block secret exfiltration and unauthorized test suite deletions.

**1.3 "Air-Gapped Enclave"** means an isolated, physically separated, or logically disconnected computing environment (such as a SCIF, SAPF, or sovereign VPC) with zero outbound network connectivity to the public internet.

**1.4 "Customer Code"** means all computer software programs, source code, scripts, configuration files, test suites, and related digital assets owned or managed by Customer and ingested by or processed through the Software.

**1.5 "Dual-Plane Context Topology"** means the architectural separation of repository context into: (a) a **Control Plane** consisting of public interface signatures, types, traits, and docstrings with stripped function bodies; and (b) an **Execution Plane** retaining full implementation bodies for active mutation targets and 1st-degree dependencies.

**1.6 "Documentation"** means the official technical specifications, user manuals, release notes, and administrator guides published by DevSuperSuite at `https://devsupersuite.web.app`.

**1.7 "Order Form"** means an ordering document, statement of work, or commercial invoice executed by both Parties that specifies the Software edition, license tier, seat quota, fees, and initial subscription or license term.

**1.8 "Software"** means the object-code binaries, scripts, and software tools licensed under this Agreement, commercially known as **DevSuperSuite / OmniKernel 5.2**, including all updates, patches, and enhancements provided hereunder.

---

### 2. LICENSE GRANT & SCOPE OF USE

**2.1 Software License Grant**: Subject to the terms of this Agreement and payment of applicable fees, DevSuperSuite hereby grants to Customer a non-exclusive, non-transferable (except as permitted under Section 12.3), worldwide license during the Term to:
- (a) Install, execute, and display the Software on Customer-owned or controlled developer workstations, servers, container clusters, and Air-Gapped Enclaves;
- (b) Utilize the Software's AST Context Slicing, AgentShield security gates, and duplex voice engine in accordance with the Documentation; and
- (c) Make a reasonable number of copies of the Software solely for archival, disaster recovery, and testing purposes.

**2.2 On-Premise Execution Invariant**: Customer acknowledges and agrees that the Software executes **100% on Customer's host silicon**. The Software does not require external SaaS endpoints, outbound network sockets, or external telemetry connections to function.

**2.3 Permitted Editions**:
- *(a) Pro Lifetime Edition*: Licensed per individual developer seat on a perpetual basis, verified via local asymmetric Ed25519 cryptographic key file.
- *(b) Enterprise VPC Cluster Edition*: Licensed for up to the designated number of seats specified on the Order Form, deployable across Customer's private cloud or internal Kubernetes infrastructure.
- *(c) Enterprise Core High-Assurance Edition*: Licensed for enterprise-wide or facility-wide deployments with unlimited seat quotas across classified or air-gapped enclaves, including FIPS 140-3 attestation.

**2.4 Restrictions**: Customer shall not: (i) reverse engineer, decompile, or disassemble the object-code binaries (except to the extent applicable law expressly prohibits such restriction); (ii) rent, lease, or sublicense the Software to third parties on a commercial service-bureau basis; or (iii) bypass, disable, or defeat the local Ed25519 cryptographic license verification routines.

---

### 3. INTELLECTUAL PROPERTY RIGHTS & OWNERSHIP

**3.1 Customer Data & Source Code Supremacy**: As between the Parties, **Customer retains absolute, sole, and exclusive ownership of all right, title, and interest (including all patent, copyright, and trade secret rights) in and to all Customer Code, repositories, AST slices, prompt payloads, and code synthesized by models utilizing the Software**. DevSuperSuite acquires zero title, ownership, or intellectual property rights in Customer Code.

**3.2 DevSuperSuite Ownership**: DevSuperSuite retains all right, title, and interest in and to the Software, the OmniKernel core engine, the Tree-sitter custom grammars, the AgentShield invariant modules, the Documentation, and all improvements, modifications, or derivative works thereof created by DevSuperSuite.

**3.3 Feedback**: Customer may, from time to time, provide suggestions, comments, or bug reports (**"Feedback"**) to DevSuperSuite. Customer grants DevSuperSuite a perpetual, irrevocable, royalty-free license to incorporate such Feedback into its standard commercial products, provided such Feedback does not identify Customer or disclose Customer Confidential Information.

---

### 4. DATA PRIVACY, ZERO DATA RETENTION & PROHIBITION ON MODEL TRAINING

**4.1 Architectural Zero Data Retention (ZDR)**: DevSuperSuite warrants and represents that:
- (a) The Software operates entirely within Customer's local computing environment and does not transmit Customer Code, tokens, or AST buffers to DevSuperSuite or any third party;
- (b) DevSuperSuite maintains zero cloud databases, caches, or persistent storage holding Customer Code; and
- (c) All volatile memory buffers holding intermediate AST slices are scrubbed and zeroized upon completion of context generation in accordance with FIPS 140-3 guidelines.

**4.2 Absolute Prohibition on Machine Learning & Model Training**: **DEVSUPERSUITE EXPRESSLY WARRANTS THAT IT DOES NOT, HAS NOT, AND SHALL NOT USE CUSTOMER CODE, REPOSITORIES, PROMPT TOKENS, DIFFS, OR INTERMEDIATE AST DATA TO TRAIN, RE-TRAIN, FINE-TUNE, ALIGN, OR VALIDATE ANY FOUNDATIONAL, GENERATIVE, OR RECURRENT ARTIFICIAL INTELLIGENCE OR MACHINE LEARNING MODEL.**

---

### 5. SECURITY INVARIANTS & AIR-GAPPED COMPLIANCE

**5.1 Local Cryptographic Attestation**: The Software utilizes asymmetric **Ed25519 digital signatures** for license validation. Verification is performed entirely locally on the host processor in under two hundred microseconds ($<200\mu\text{s}$) without network pings or telemetry.

**5.2 AgentShield Protection**: The Software includes local pre-commit hooks that enforce:
- (a) **Cryptographic Secret Interception**: Halting staged commits in CPU registers when candidate string literals exhibit Shannon entropy $H \ge 4.50\text{ bits/char}$; and
- (b) **`INVARIANT_TEST_PRESERVATION`**: Aborting automated commits that delete unit test assertions (`AssertNodes`) with POSIX Exit Code 2.

**5.3 Air-Gapped SCIF Readiness**: DevSuperSuite warrants that the Software is compatible with air-gapped Sensitive Compartmented Information Facilities (SCIFs), ITAR enclaves, and CMMC 2.0 Level 2/3 environments, and enforces Kubernetes zero-outbound NetworkPolicies (`egress: []`).

---

### 6. FEES, INVOICING & PAYMENT TERMS

**6.1 License Fees**: Customer shall pay the license fees set forth in the applicable Order Form. Unless otherwise specified on the Order Form:
- (a) Pro Lifetime licenses are billed upon checkout via credit card or digital invoice;
- (b) Enterprise VPC and Enterprise Core licenses are billed annually in advance; and
- (c) All fees are denominated in United States Dollars (USD), Indian Rupees (INR), or Euros (EUR) as stated on the Order Form.

**6.2 Invoicing & Payment**: For invoiced agreements, payment is due **Net thirty (30) days** from the invoice date. Late payments shall accrue interest at the rate of one percent (1.0%) per month or the maximum rate permitted by law, whichever is lower.

**6.3 Taxes**: Fees are exclusive of applicable sales, use, excise, value-added (VAT), or withholding taxes. Customer shall be responsible for all such taxes, excluding taxes based on DevSuperSuite's net income.

---

### 7. WARRANTIES & DISCLAIMERS

**7.1 Performance Warranty**: DevSuperSuite warrants that for a period of **ninety (90) days** following initial delivery, the Software will perform substantially in accordance with the specifications set forth in the Documentation under normal enterprise operating conditions. Customer's sole and exclusive remedy for breach of this warranty shall be for DevSuperSuite to use commercially reasonable efforts to correct the non-conforming functionality, or if unable to do so within thirty (30) days, to refund unearned prepaid license fees on a pro-rata basis.

**7.2 Malicious Code Warranty**: DevSuperSuite warrants that the Software does not contain any malware, viruses, trojan horses, backdoors, time-bombs, or undisclosed code designed to disrupt, disable, or permit unauthorized access to Customer's systems.

**7.3 Generative AI Output Disclaimer**: The Parties acknowledge that DevSuperSuite operates as a deterministic syntactic context compiler and invariant security gate. **To the extent Customer routes AST-sliced context to third-party generative artificial intelligence models (e.g., Anthropic Claude, OpenAI GPT, Google Gemini, or local models), DevSuperSuite disclaims all warranties regarding the syntactic accuracy, fitness for a particular purpose, or compilability of third-party model completions.** Customer retains sole responsibility for reviewing, compiling, and testing all generated code before production deployment.

---

### 8. MUTUAL INDEMNIFICATION

**8.1 DevSuperSuite IP Indemnification**: DevSuperSuite shall defend, indemnify, and hold harmless Customer and its officers, directors, and employees from and against any third-party claims, suits, or proceedings alleging that the core Software (excluding Customer Code and third-party AI completions) infringes any valid patent, copyright, or trademark. DevSuperSuite shall pay all damages and costs finally awarded against Customer or agreed to in a settlement approved in writing by DevSuperSuite.

**8.2 Mitigation Remedies**: If the Software becomes, or in DevSuperSuite's reasonable opinion is likely to become, the subject of an infringement claim, DevSuperSuite may at its option and expense: (a) procure for Customer the right to continue using the Software; (b) replace or modify the Software so that it becomes non-infringing while maintaining substantially equivalent functionality; or (c) if neither (a) nor (b) is commercially feasible, terminate this Agreement and refund unearned prepaid fees on a pro-rata basis.

**8.3 Customer Indemnification**: Customer shall defend, indemnify, and hold harmless DevSuperSuite from and against any third-party claims arising out of: (a) Customer Code; (b) Customer's breach of Section 11 (Export Compliance); or (c) modifications made to the Software by anyone other than DevSuperSuite.

**8.4 Indemnification Procedure**: Each Party's indemnification obligations are conditioned on the indemnified Party: (i) providing prompt written notice of the claim; (ii) granting the indemnifying Party sole control over the defense and settlement (provided settlements do not impose admission of liability or monetary obligation on the indemnified Party); and (iii) providing reasonable cooperation at the indemnifying Party's expense.

---

### 9. LIMITATION OF LIABILITY

**9.1 Consequential Damages Waiver**: **TO THE MAXIMUM EXTENT PERMITTED BY LAW, NEITHER PARTY NOR ITS AFFILIATES SHALL BE LIABLE FOR ANY INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING LOSS OF PROFITS, LOSS OF REVENUE, LOSS OF REPUTATION, LOSS OF DATA, OR BUSINESS INTERRUPTION, REGARDLESS OF THEORY OF LIABILITY (WHETHER IN CONTRACT, TORT, STRICT LIABILITY, OR OTHERWISE), EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.**

**9.2 Aggregate Liability Cap**: **EXCEPT FOR INDEMNIFICATION OBLIGATIONS UNDER SECTION 8 OR A PARTY'S WILLFUL MISCONDUCT, EACH PARTY'S TOTAL AGGREGATE LIABILITY ARISING OUT OF OR RELATED TO THIS AGREEMENT SHALL BE STRICTLY LIMITED TO THE TOTAL AMOUNT ACTUALLY PAID BY CUSTOMER UNDER THE APPLICABLE ORDER FORM IN THE TWELVE (12) MONTHS PRECEDING THE EVENT GIVING RISE TO LIABILITY.**

---

### 10. TERM, RENEWAL & TERMINATION

**10.1 Term**: This Agreement commences on the Effective Date and continues for the initial term specified in the Order Form (typically twelve (12) months). For enterprise subscriptions, the Agreement shall automatically renew for additional successive twelve (12) month periods unless either Party provides written notice of non-renewal at least **sixty (60) days** prior to the expiration of the then-current term.

**10.2 Termination for Cause**: Either Party may terminate this Agreement immediately upon written notice if: (a) the other Party commits a material breach of this Agreement and fails to cure such breach within thirty (30) days of receiving written notice; or (b) the other Party becomes insolvent, enters receivership, or files for bankruptcy protection.

**10.3 Effect of Termination**: Upon termination or expiration of this Agreement: (a) all active license rights terminate; (b) Customer shall discontinue use of the Software; and (c) each Party shall return or certify destruction of all Confidential Information of the other Party. Sections 1, 3, 4, 6 (for accrued fees), 7.3, 9, 10.3, and 12 shall survive termination.

---

### 11. EXPORT COMPLIANCE & DEFENSE REGULATORY MANDATES

**11.1 Export Laws**: Customer warrants that it shall comply with all applicable United States and international export control laws and regulations, including the International Traffic in Arms Regulations (ITAR, 22 CFR §§ 120–130) and Export Administration Regulations (EAR, 15 CFR §§ 730–774).

**11.2 Sanctions**: Customer represents and warrants that neither it nor any of its Affiliates or users is listed on any U.S. government restricted-party list (including OFAC Specially Designated Nationals List, Entity List, or Denied Persons List).

---

### 12. GENERAL PROVISIONS

**12.1 Governing Law & Venue**: This Agreement shall be governed by and construed in accordance with the laws of the **State of Delaware**, without regard to its conflict of laws principles. The Parties agree to the exclusive jurisdiction of the state and federal courts located in Wilmington, Delaware. **THE PARTIES HEREBY MUTUALLY WAIVE TRIAL BY JURY IN ANY ACTION ARISING HEREFROM.**

**12.2 Dispute Resolution & Arbitration**: Any dispute arising out of or related to this Agreement that cannot be resolved through good-faith negotiation within thirty (30) days shall be settled by binding arbitration administered by the American Arbitration Association (AAA) under its Commercial Arbitration Rules, before a single neutral arbitrator.

**12.3 Assignment**: Neither Party may assign or transfer this Agreement without the prior written consent of the other Party, except that either Party may assign this Agreement in its entirety without consent to an Affiliate or in connection with a merger, acquisition, corporate reorganization, or sale of substantially all of its assets, provided the assignee is not a direct competitor of the non-assigning Party.

**12.4 Severability & Entire Agreement**: If any provision of this Agreement is held to be invalid or unenforceable, the remaining provisions shall continue in full force and effect. This Agreement, together with all executed Order Forms, constitutes the complete and exclusive agreement between the Parties with respect to the subject matter hereof, superseding all prior proposals, understandings, and purchase order terms.

---

### EXHIBIT A: SERVICE LEVEL AGREEMENT (SLA) & SUPPORT POLICY

1. **VPC Cluster Availability**: For Enterprise VPC deployments, DevSuperSuite commits to a **99.9% availability SLA** for the local container control plane, excluding scheduled maintenance (which shall be announced with at least 48 hours notice).
2. **Support Channels & Response Times**:
   - **Severity 1 (System Down / Workstation Halt)**: Initial response within **one (1) hour**; 24/7 dedicated compiler engineering triage.
   - **Severity 2 (Degraded Performance / AST Slicing Failure)**: Initial response within **four (4) hours** during standard business hours.
   - **Severity 3 (General Inquiries / Documentation)**: Initial response within **twenty-four (24) hours**.
3. **Dedicated Communication Bridge**: Enterprise Core customers receive a private, encrypted Slack or Microsoft Teams channel directly with Lead Systems Architects.

---

### EXHIBIT B: SOURCE CODE ESCROW AGREEMENT (NCC GROUP / IRON MOUNTAIN)

1. **Escrow Deposit**: DevSuperSuite maintains a master source code escrow deposit with **NCC Group / Iron Mountain**. Enterprise Core High-Assurance licensees may be registered as designated third-party beneficiaries.
2. **Deposit Contents**: Semi-annual deposits of the full Rust/C compiler source code, Tree-sitter custom grammar definitions, AgentShield entropy algorithms, and build toolchains.
3. **Release Triggers**: Escrow materials shall be released to Customer solely upon: (a) entry of an order for relief under federal bankruptcy laws without a plan of reorganization; (b) complete cessation of business operations by DevSuperSuite without an assignment to a successor entity; or (c) failure to support the Software following an uncured material breach.

---

### EXHIBIT C: FORM OF ENTERPRISE ORDER FORM (SAMPLE)

```
===================================================================================
                       DEVSUPERSUITE ENTERPRISE ORDER FORM
===================================================================================
Customer Legal Name:    [ Enterprise Technology Corp. ]
Agreement Reference:    Master Services Agreement Ref: DSS-MSA-STANDARD-2026-V52
Effective Date:         [ Effective Date: YYYY-MM-DD ]
Billing Contact Email:  [ procurement@enterprise.corp ]

LICENSED SOFTWARE & TIERS:
[ ] Pro Lifetime Fleet Voucher   Qty: [  ] Seats @ $29 USD / Seat (Perpetual)
[X] Enterprise VPC Cluster       Up to 100 Seats: $15,000 USD / Year
[ ] Enterprise Core High-Assur   Unlimited Seats (SCIF / FIPS): $35,000 USD / Year

TOTAL ANNUAL CONTRACT VALUE:     $15,000.00 USD
PAYMENT TERMS:                   Net 30 Days from Invoice Date
INITIAL SUBSCRIPTION TERM:       Twelve (12) Months from Effective Date

IN WITNESS WHEREOF, the Parties have executed this Order Form by authorized signers.

DEVSUPERSUITE OFFICIAL / OMNIKERNEL LABS   CUSTOMER: [ ENTERPRISE TECH CORP ]
Signature: ___________________________    Signature: ___________________________
Title: Lead Legal Counsel & VP Commercial  Title: Chief Information Officer / VP
Date:  ___________________________        Date:  ___________________________
===================================================================================
```

---

*Copyright © 2026 DevSuperSuite Legal Counsel & Commercial Contracting Desk. All rights reserved. Master institutional contracting documentation.*

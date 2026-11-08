# DevSuperSuite Hacker News 'Show HN' Playbook
**Ranking Algorithm Mechanics, Anti-Sensationalism Guidelines & High-Gravity Defense**  
**Submitting Entity**: DevSuperSuite Hacker News Desk (`hn@devsupersuite.com`)  
**Compliance**: 100% Brand Anonymity Protocol Verified | Zero Founder Personal Disclosures  
**Interactive CDN Demo**: [https://devsupersuite.web.app](https://devsupersuite.web.app)  
**Community VIP Voucher**: `HN-SHOW-VIP` ($24 Pro Lifetime / regular $29)

---

## 1. The Hacker News Ranking Algorithm & Gravity Formula

Hacker News uses an open, elegant ranking algorithm designed to surface high-signal technical content while penalizing stale submissions over time:

$$\text{Score} = \frac{(P - 1)^G}{(T + 2)^\gamma}$$

Where:
- **$P$**: Upvotes (Points) received by the submission. (Minus 1 to negate the submitter's automatic upvote).
- **$G$**: Base gravity exponent (typically $G = 0.8$ for standard posts, $G = 1.0$ for Show HNs).
- **$T$**: Age of the post in hours since submission.
- **$\gamma$ (Gamma)**: The time penalty exponent, calibrated to **$1.8$**.

```
+---------------------------------------------------------------------------------------+
|                    HACKER NEWS GRAVITY SCORE DECAY CURVE (P = 50)                     |
+---------------------------------------------------------------------------------------+
|  Hour T=0:  Score = 49 / (2)^1.8       = ~14.07   (Front Page Peak: Position 1-3)     |
|  Hour T=2:  Score = 49 / (4)^1.8       = ~4.04    (Front Page Core: Position 5-10)    |
|  Hour T=6:  Score = 49 / (8)^1.8       = ~1.16    (Mid Front Page: Position 15-22)    |
|  Hour T=12: Score = 49 / (14)^1.8      = ~0.42    (Second Page Decay: Position 30+)   |
|  Hour T=24: Score = 49 / (26)^1.8      = ~0.14    (Archive Fall-off)                  |
+---------------------------------------------------------------------------------------+
```

### Critical Operational Takeaway:
To stay on the Front Page (positions 1–30) for 12+ hours, a submission must maintain **continuous karma velocity**: it requires approximately **8 to 15 upvotes per hour** alongside an active, authentic comment thread.

---

## 2. HN Anti-Spam Heuristics & Shadow-Ban Triggers

Hacker News operates some of the most aggressive automated spam and vote-manipulation filters on the web. Violating these heuristics triggers silent downranking or an outright shadow-ban:

### Heuristic 1: The Automated Title Flag Filter (Sensationalism Triggers)
Hacker News automated filters immediately downrank or flag submissions containing marketing buzzwords. **Never** include:
- ❌ *"Revolutionary"*, *"Disrupt"*, *"Game-changing"*, *"Next-gen"*
- ❌ *"AI-powered"*, *"Magical"*, *"Must-have"*, *"Supercharge"*
- ❌ *"Free trial"*, *"Sign up now"*, *"Limited offer"*
- ❌ ALL-CAPS words, exclamation marks (`!`), or clickbait questions (*"Why everyone is wrong about..."*).

**Approved Show HN Title Format**:
```text
Show HN: DevSuperSuite – Local AST interface slicer & invariant guard for AI agents
```
*(74 characters, strictly under the 80-character boundary, objective, factual, zero hype).*

### Heuristic 2: Voting Ring & Coordinated Upvoting Detection
The HN software actively monitors:
1. **IP & ASN Clustering**: Multiple upvotes originating from the same IP, office Wi-Fi, or VPN subnet within a short window.
2. **Referral Header Detection**: Upvotes originating directly from a shared link (e.g., Slack, Discord, Twitter, or WhatsApp). The HN algorithm completely ignores or discounts upvotes that arrive with external `Referer` headers.
   > **Mandatory Rule**: Never post direct submission links to external chat rooms. Tell supporters to find the submission organically on `news.ycombinator.com/show`.
3. **Upvote-to-Comment Ratio**: A submission with 30 upvotes and 0 comments is flagged as unnatural. Authentic front-page posts always feature active comment discussions.
4. **New Account Weighting**: Accounts created within the past 30 days or with karma <20 have near-zero upvote weight.

---

## 3. Optimal Submission Timing Windows

Hacker News activity peaks during US West Coast morning hours when Silicon Valley and European engineers are simultaneously active:

```
+-------------------------------------------------------------------------------+
|                       OPTIMAL HN LAUNCH TIME WINDOWS                          |
+-------------------------------------------------------------------------------+
|  TIER 1 (GOLDEN WINDOW):                                                      |
|  • Tuesday:   06:30 AM - 08:30 AM PST  (14:30 - 16:30 UTC)                    |
|  • Wednesday: 06:30 AM - 08:30 AM PST  (14:30 - 16:30 UTC)                    |
|                                                                               |
|  TIER 2 (STRONG BACKUP):                                                      |
|  • Thursday:  07:00 AM - 09:00 AM PST  (15:00 - 17:00 UTC)                    |
|                                                                               |
|  PROHIBITED SUBMISSION PERIODS:                                               |
|  • Friday Afternoon / Weekends (Lower technical traffic, low karma velocity). |
|  • Monday Morning (Crowded with major tech news and VC announcements).       |
+-------------------------------------------------------------------------------+
```

---

## 4. The Maker's Opening Submission Comment Architecture

On Hacker News, the maker's initial comment sets the entire tone of the thread. A weak or defensive comment invites cynicism; a transparent, deeply technical comment garners respect.

### The 5 Elements of an Ironclad Maker Comment:
1. **The Origin Story & Technical Motivation**: Explain the exact engineering pain that led to building the tool (e.g. Attention Sink Dilution on 50k+ LOC monorepos, agents deleting unit tests).
2. **The Architecture Diagram (ASCII)**: Provide a clean ASCII diagram illustrating the local pipeline. HN engineers love text diagrams.
3. **Reproducible Benchmarks**: Share concrete numbers (e.g., -83.0% token reduction across 25 production repositories, 2.14ms/1k LOC).
4. **Local-First & Zero Egress Guarantee**: Emphasize that code never leaves developer memory; highlight the client-side WebAssembly demo at `https://devsupersuite.web.app`.
5. **Vulnerability & Community Discussion Prompt**: Ask for constructive critique on specific technical trade-offs (e.g., Tree-sitter query optimization, error recovery).

---

## 5. Engaging the 5 Classic HN Skeptic Archetypes

During a live front-page thread, 90% of comments will come from 5 recognizable archetypes. Maintainers must respond with calm, authoritative technical depth without ever sounding defensive:

### Archetype 1: The ripgrep / UNIX Purist
- *Their View*: *"Why not just use ripgrep and ctags? This is bloat."*
- *Winning Response*: Acknowledge ripgrep's excellence at byte-stream search, then explain why ctags and regex lack concrete syntax tree scope. Explain how Tree-sitter elides loop bodies while preserving type declarations in sub-2.4ms.

### Archetype 2: The AI Wrapper Cynic
- *Their View*: *"Just another flimsy Next.js wrapper calling OpenAI."*
- *Winning Response*: Clarify that DevSuperSuite does **not** call OpenAI or any cloud LLM. It is a local C/Rust compiler and pre-commit security utility running entirely on the developer's CPU. Invite them to inspect the browser demo in DevTools.

### Archetype 3: The Type-System Language Lawyer
- *Their View*: *"How does this work on dynamic languages like Python or JavaScript?"*
- *Winning Response*: Explain how Tree-sitter parses structural syntax independently of type declarations. Detail how Python class headers, decorators, and docstrings are preserved while method suites are stubbed with `...`.

### Archetype 4: The AGPL / Open Source Fundamentalist
- *Their View*: *"Why isn't this 100% free under AGPLv3? Why charge for dev tools?"*
- *Winning Response*: Explain our sustainable software philosophy: zero venture capital, zero telemetry tracking, zero $20/month SaaS subscriptions. Point out that the WebAssembly browser demo and Tree-sitter queries are 100% open and free.

### Archetype 5: The Benchmark Auditor
- *Their View*: *"Where are the exact hardware specs and reproducible test harnesses?"*
- *Winning Response*: Provide exact hardware specs (Apple M3 Max, AMD Ryzen 9 7950X, DDR5), criterion.rs test harnesses, and link to the open benchmark runner at `https://devsupersuite.web.app`.

---

## 6. Live Thread Monitoring & Emergency Response Cadence

- **First 60 Minutes (The Velocity Crucible)**:
  - Refresh the thread every 3 minutes.
  - Respond to every comment within 5 to 10 minutes. Early comment velocity signals to the algorithm that the submission is generating high-value discussion.
- **Hours 1 to 6 (Front Page Trajectory)**:
  - Keep tone humble, analytical, and respectful. Never downvote or argue defensively with cynical comments.
  - If a user reports a bug or edge-case parsing failure, thank them immediately, reproduce it, and share the exact Tree-sitter query fix.
- **Hours 6 to 18 (Sustained Inbound Conversion)**:
  - Thousands of engineers will visit `https://devsupersuite.web.app`.
  - Ensure the client-side WebAssembly demo runs smoothly with zero CDN errors.

---
*DevSuperSuite Hacker News Desk — 100% Brand Anonymity Protocol Verified.*

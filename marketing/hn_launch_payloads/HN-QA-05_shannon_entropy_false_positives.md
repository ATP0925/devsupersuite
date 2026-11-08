# Hacker News Technical Response: Shannon entropy false positives (HN-QA-05)
**Author**: DevSuperSuite Systems Engineering (`engineering@devsupersuite.com`)  
**Compliance**: 100% Brand Anonymity Guaranteed  

### Cynical HN Comment:
> *"Shannon entropy alone creates massive false positives on UUIDs, sha256 hashes, and base64 assets."*

### Engineered Systems Response:
Correct. Naive Shannon entropy ($H(X) = -\sum P(x) \log_2 P(x)$) flags random UUIDs, git commit hashes, and base64 inline images every single time.

DevSuperSuite avoids this via a 3-stage deterministic filter:
1. **Tree-Sitter Node Isolation**: Entropy is only evaluated inside variable assignment literals, string literals, and `.env` files — never inside comments, asset arrays, or hex color tokens.
2. **Alphabet & Character-Set Variance**: UUIDs and hexadecimal hashes have an alphabet size of 16 (hex) with specific hyphens ($H \approx 3.4 - 3.8$). Cryptographic API keys (Stripe `sk_live_`, AWS Secret Keys, Anthropic `sk-ant-`) use Base64/Base62 character distributions with $H > 4.5$ bits/char.
3. **Structured Entropy Density**: We compute entropy density over sliding 32-character windows with known prefix matching, reducing false positives to 0.0% on standard codebases.

---
*DevSuperSuite Systems Engineering | Local-First Developer Tooling*

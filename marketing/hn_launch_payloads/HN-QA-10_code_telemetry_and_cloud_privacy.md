# Hacker News Technical Response: Code telemetry and cloud privacy (HN-QA-10)
**Author**: DevSuperSuite Systems Engineering (`engineering@devsupersuite.com`)  
**Compliance**: 100% Brand Anonymity Guaranteed  

### Cynical HN Comment:
> *"Does this tool send my code or AST graphs to your servers?"*

### Engineered Systems Response:
Zero code leaves your machine. DevSuperSuite contains no analytics, no telemetry daemons, and no cloud relay servers. 

The binary executes 100% locally on localhost. It does not require network access to slice ASTs or scan for secrets. You can verify this with `tcpdump`, Wireshark, or by running the CLI in a completely air-gapped container with networking disabled.

---
*DevSuperSuite Systems Engineering | Local-First Developer Tooling*

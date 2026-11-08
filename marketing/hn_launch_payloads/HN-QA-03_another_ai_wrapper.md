# Hacker News Technical Response: Another AI wrapper? (HN-QA-03)
**Author**: DevSuperSuite Systems Engineering (`engineering@devsupersuite.com`)  
**Compliance**: 100% Brand Anonymity Guaranteed  

### Cynical HN Comment:
> *"Is this just another AI wrapper calling OpenAI APIs under the hood?"*

### Engineered Systems Response:
No. DevSuperSuite contains zero LLM API calls in its core engine and does not require an OpenAI or Anthropic API key.

It is a local systems utility compiled with native C bindings to Tree-sitter grammars and runs 100% offline on your localhost. It operates as:
1. A local CLI and Git pre-commit hook that prunes staged code before it ever reaches Cursor, Claude Code, or your git remote.
2. A Shannon entropy cryptographic scanner ($H(X) > 4.5$ bits/char) to block leaked keys.
3. A diff invariant validator enforcing that autonomous agents don't delete unit tests.

You can inspect the offline behavior in our interactive sandbox at https://devsupersuite.web.app (the parser runs client-side in WebAssembly).

---
*DevSuperSuite Systems Engineering | Local-First Developer Tooling*

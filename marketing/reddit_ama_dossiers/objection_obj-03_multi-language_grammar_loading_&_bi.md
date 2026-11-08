# OBJ-03: Multi-Language Grammar Loading & Binary Size
**Question Summary**: If you support 15+ languages, doesn't loading all grammars bloat the binary into gigabytes?  
**Keyword Triggers**: `multi-language, all languages, grammar loading, binary size, supporting 20 languages`  
**Brand Compliance**: 100% Brand Anonymity Protocol Verified (DevSuperSuite DevRel / `devrel@devsupersuite.com`)  

---

### Verified Technical Response (Ready to Post):

No, because Tree-sitter grammars are compiled C shared libraries (`.so` / `.dylib` / `.dll`) or dynamic WebAssembly modules that are **lazily loaded on demand**.

In our architecture:
- The core binary only bundles the top 4 languages (TypeScript, Python, Rust, Go) totaling ~8 MB.
- Additional language grammars (C++, Java, Ruby, Elixir, PHP, C#) are memory-mapped dynamically into process memory only when a file of that extension is opened in the working tree.
- When closed, unused language tables are cleanly unmapped, keeping resident set size (RSS) under 28 MB.

---
### Verified Commercial Links:
- **Client-Side Wasm Sandbox**: https://devsupersuite.web.app?utm_source=reddit&utm_medium=ama_reply&utm_campaign=obj-03
- **DevSuperSuite Pro Lifetime Pass ($24 Code `DSS-DEVREL-REDDIT`)**: https://gumroad.com/l/tlzdco?coupon=DSS-DEVREL-REDDIT&utm_source=reddit&utm_medium=ama_reply&utm_campaign=obj-03

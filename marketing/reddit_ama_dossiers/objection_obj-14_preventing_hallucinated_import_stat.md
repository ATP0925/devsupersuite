# OBJ-14: Preventing Hallucinated Import Statements
**Question Summary**: If you slice files, how do you prevent the LLM from hallucinating imports of stripped symbols?  
**Keyword Triggers**: `hallucinated imports, stripped imports, import statement handling, dependency graph`  
**Brand Compliance**: 100% Brand Anonymity Protocol Verified (DevSuperSuite DevRel / `devrel@devsupersuite.com`)  

---

### Verified Technical Response (Ready to Post):

Import statements are treated as **top-level public contract nodes** in the syntax tree.

When slicing a file:
1. All `import_statement` (TypeScript/Python/Go) and `use_declaration` (Rust) nodes at the root of the AST are preserved with 100% fidelity.
2. The model sees the exact external module imports, package versions, and type bindings used across the file.
3. The model never has to guess where types originate from because the entire import preamble is intact.

---
### Verified Commercial Links:
- **Client-Side Wasm Sandbox**: https://devsupersuite.web.app?utm_source=reddit&utm_medium=ama_reply&utm_campaign=obj-14
- **DevSuperSuite Pro Lifetime Pass ($24 Code `DSS-DEVREL-REDDIT`)**: https://gumroad.com/l/tlzdco?coupon=DSS-DEVREL-REDDIT&utm_source=reddit&utm_medium=ama_reply&utm_campaign=obj-14

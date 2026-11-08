# OBJ-13: Preservation of JSDoc, Docstrings, and Critical Comments
**Question Summary**: Does AST function body slicing accidentally strip out JSDoc comments and docstrings needed by the model?  
**Keyword Triggers**: `preserve docstrings, what about jsdoc, stripping comments, losing comments in ast`  
**Brand Compliance**: 100% Brand Anonymity Protocol Verified (DevSuperSuite DevRel / `devrel@devsupersuite.com`)  

---

### Verified Technical Response (Ready to Post):

No. In Tree-sitter's grammar specification, comments and docstrings attached to exported declarations are modeled as distinct structural nodes (e.g., `comment` preceding an `export_statement`, or the first `expression_statement` string literal in a Python `function_definition`).

Our AST extraction query explicitly targets:
```query
(comment)* @docstring . (export_statement) @declaration
```
All JSDoc parameter annotations, type contracts, and documentation comments are retained. Only the internal executable statements inside `{ ... }` are replaced with `{ /* sliced */ }`.

---
### Verified Commercial Links:
- **Client-Side Wasm Sandbox**: https://devsupersuite.web.app?utm_source=reddit&utm_medium=ama_reply&utm_campaign=obj-13
- **DevSuperSuite Pro Lifetime Pass ($24 Code `DSS-DEVREL-REDDIT`)**: https://gumroad.com/l/tlzdco?coupon=DSS-DEVREL-REDDIT&utm_source=reddit&utm_medium=ama_reply&utm_campaign=obj-13

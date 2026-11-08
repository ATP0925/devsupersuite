# OBJ-07: Handling Dynamic Languages (Python, JavaScript) Without Static Types
**Question Summary**: How does your AST pruner handle dynamic languages like untyped Python or JavaScript?  
**Keyword Triggers**: `dynamic languages, python without types, javascript untyped, duck typing`  
**Brand Compliance**: 100% Brand Anonymity Protocol Verified (DevSuperSuite DevRel / `devrel@devsupersuite.com`)  

---

### Verified Technical Response (Ready to Post):

Tree-sitter does not require static type declarations; it operates on the **structural grammar** of the language.

For dynamic languages:
- **Python**: Tree-sitter queries extract `function_definition` parameters, default arguments, return statements, class definitions, and decorator chains (`@property`, `@dataclass`), while replacing the inner block with `pass  # sliced`. Docstrings (triple-quoted strings) are explicitly preserved.
- **JavaScript**: It extracts exported function declarations, object destructuring parameters, and JSDoc comments while replacing method bodies with `{ /* sliced */ }`.

Even without static types, an LLM only needs the parameter names, docstrings, and call interfaces to write correct integration logic.

---
### Verified Commercial Links:
- **Client-Side Wasm Sandbox**: https://devsupersuite.web.app?utm_source=reddit&utm_medium=ama_reply&utm_campaign=obj-07
- **DevSuperSuite Pro Lifetime Pass ($24 Code `DSS-DEVREL-REDDIT`)**: https://gumroad.com/l/tlzdco?coupon=DSS-DEVREL-REDDIT&utm_source=reddit&utm_medium=ama_reply&utm_campaign=obj-07
